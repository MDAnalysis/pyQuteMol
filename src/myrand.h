
#ifndef __MYRAND_H
#define __MYRAND_H

float myrand() {
	static int k = 0;
  k += 1231543214;
	return ((k%12421)/12421.0);
}

#endif
