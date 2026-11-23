/* Program Description:
 * 输入一个下标，查出那一格的分数。
 * 分数表有 4 格，下标从 0 开始：
 *   0 -> 70    1 -> 80    2 -> 90    3 -> 100
 * 下标不在 0 到 3 之间时，要输出“下标超出范围”。
 * 课堂例子：合法下标、负数、大于 4 的下标都正常。
 * 判断写成了 index > 4，下标正好等于 4 时会读到表外面。
 */

#include <iostream>

int main() {
    int scores[4] = {70, 80, 90, 100};
    int index;

    std::cout << "请输入下标 > ";
    std::cin >> index;

    if (index < 0 || index > 4) {
        std::cout << "下标超出范围\n";
        return 0;
    }
    std::cout << scores[index] << "\n";
    return 0;
}
