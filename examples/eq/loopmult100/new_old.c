int foo1(int a, int b) {
	int c = 0;
	for (int i=0; i<a; ++i)
		c += b;
	return c;}

int foo2(int a, int b) {
	int c = 0;
	for (int i=0; i<b; ++i)
		c += a;
	return c;}

/*
int main(int x, char*argv[]) {
	if (x>=85 && x<115)
    //assert(foo1(x,100) == 0);
    return 0;
	assert(foo1(x,100) == 0);
  //assert(foo1(x,100) == foo2(x,100));
	return 0;
}*/

int main(int x, char*argv[]) {
	assert(foo1(x,100) == 0);
	return 0;
}
