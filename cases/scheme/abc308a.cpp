/* 这道题在做什么
 * 输入 8 个整数。三条都满足就输出 Yes，否则输出 No：
 *   1. 从左到右不下降，允许相邻两个数相等
 *   2. 每个数都在 100 到 675 之间，包含 100 和 675
 *   3. 每个数都是 25 的倍数
 * 算法：从左到右看相邻的两个数，再单独检查最后一个数。
 * 题目：https://atcoder.jp/contests/abc308/tasks/abc308_a
 * 许可见 CONDEFECTS-LICENSE.txt。
 */

#include <iostream>

int main() {
    int s[8];
    for (int i = 0; i < 8; ++i)
        std::cin >> s[i];
    for (int i = 0; i < 7; ++i) {
        if (s[i] >= s[i + 1] || s[i] % 25 || s[i] < 100 || s[i] > 675) {
            std::cout << "No\n";
            return 0;
        }
    }
    if (s[7] % 25 || s[7] < 100 || s[7] > 675)
        std::cout << "No\n";
    else
        std::cout << "Yes\n";
    return 0;
}
