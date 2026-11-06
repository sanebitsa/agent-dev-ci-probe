#include <cassert>

constexpr int add(int left, int right) { return left + right; }

int main() {
  assert(add(2, 3) == 5);
  return 0;
}
