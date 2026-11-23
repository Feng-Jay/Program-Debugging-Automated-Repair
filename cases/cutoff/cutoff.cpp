/* Program Description:
 * 输入一个整数分数。60 分及以上输出 pass，否则输出 fail。
 * 课堂泛化例子：用来检查修复方法有没有把补丁写死在某一个旧案例上。
 * 有缺陷的版本写成了 score > 60，正好 60 分会输出 fail。
 */

#include <iostream>

int main() {
    int score;
    std::cin >> score;
    if (score > 60)
        std::cout << "pass\n";
    else
        std::cout << "fail\n";
    return 0;
}
