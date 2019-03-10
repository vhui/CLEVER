import sys
import argparse
import shlex, subprocess

from pysmt.smtlib.parser import SmtLibParser
from pysmt.smtlib.script import SmtLibScript
import pysmt.smtlib.commands as smtcmd

from pysmt.walkers import IdentityDagWalker
from pysmt.operators import SYMBOL
#from pysmt.shortcuts import Iff, Equals, Symbol
from pysmt.shortcuts import Not, Equals, BVZero
from pysmt.shortcuts import get_env, substitute

#This function modifies our IdentityDagWalker to substitute known symbols in summary
symbol_table = {}
def walk_symbol(self, formula, args, **kwargs):
  symbol_subs = self.mgr.Symbol(formula.symbol_name(), formula.symbol_type())
  if formula.symbol_name() in symbol_table:
    symbol_subs = symbol_table[formula.symbol_name()]
  return symbol_subs

IdentityDagWalker.set_handler(walk_symbol, SYMBOL)


def bmc_summarize(smtin_filename = "UNNAMED_in.smt2", smtout_filename = "UNNAMED_out.smt2"):

  parser = SmtLibParser()
  with open(smtin_filename, 'r+') as f:
    smtlib = parser.get_script(f)

  asserts = list(smtlib.filter_by_command_name([smtcmd.ASSERT]))
  defs = list(smtlib.filter_by_command_name([smtcmd.DEFINE_FUN]))
  decls = list(smtlib.filter_by_command_name([smtcmd.DECLARE_FUN]))

  #print(smtlib.get_last_formula())
  func_summary = None
  for stmt in asserts:
    #print(stmt)
    if stmt.args[0].is_iff() or stmt.args[0].is_equals():
      assert stmt.args[0].arg(0).is_symbol() and stmt.args[0].arg(1) 
      #print("Assertion on a symbolic equation.")
      symbol_table[stmt.args[0].arg(0).symbol_name()] = stmt.args[0].arg(1)
    #pattern match for assertion on summary (PROPERTY: !(... = 0) )
    if stmt.args[0].is_not():
      safety_prop = stmt.args[0].arg(0)
      if (safety_prop.is_equals() or safety_prop.is_iff()) and safety_prop.arg(1).is_bv_constant(0):
        func_summary = safety_prop.arg(0)

  summarizer = IdentityDagWalker()
  try:
    summary = summarizer.walk(func_summary)
  except:
    print("Could not summarize the summary.")
    import pdb; pdb.set_trace() #Exception raised.
  #import pdb; pdb.set_trace() #PLAY WITH REPRESENTATION in pdb if desired


  #Print to stdout in SMTLib format:
  print(";Summary looks like:\n")
  print(summary.to_smtlib(False) + "\n")

  #Rewrite back into SMTLibScript, then print simplification back to file
  newscript = SmtLibScript()
  newscript.add(smtcmd.SET_OPTION, [':produce-models', 'true'])
  newscript.add(smtcmd.SET_LOGIC, ["QF_AUFBV"])
  for decl in decls:
    newscript.add_command(decl)
  newscript.add(smtcmd.ASSERT, [Not(Equals(summary, BVZero(width=32)))]) #NOTE: need the !(...=0) structure again, for the assertion
  newscript.add(smtcmd.CHECK_SAT, [])
  newscript.add(smtcmd.EXIT, [])
  
  with open(smtout_filename, 'w+') as f:
    newscript.serialize(f, daggify=False)


if __name__ == "__main__":
  argv = sys.argv[1:]
  
  parser = argparse.ArgumentParser()
  parser.add_argument('--function', nargs='?', default=None)
  parser.add_argument('--unwinds', type=int, default=10)
  parser.add_argument('--infile', nargs='?', default='UNNAMED_in.smt2')
  parser.add_argument('--outfile', nargs='?', default='UNNAMED_out.smt2')

  io_args = parser.parse_args()
  function = io_args.function
  unwinds = io_args.unwinds
  infile = io_args.infile
  outfile = io_args.outfile
  
  if function:
    temp_filename = function + "_SMTout.smt2"
    args = shlex.split("cbmc %s --no-unwinding-assertions --unwind %d --smt2 --outfile %s" % (function, unwinds, temp_filename))
    proc = subprocess.Popen(args)
    out, err = proc.communicate(timeout=180)
    bmc_summarize(temp_filename, outfile)
  elif infile:
    bmc_summarize(infile, outfile)
  else:
    bmc_summarize()
    #should not happen?

###DRAFT WORK
"""for decl in decls:
    print(decl.serialize(sys.stdout, daggify=False))"""

