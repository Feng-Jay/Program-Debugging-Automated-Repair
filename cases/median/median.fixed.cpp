/* Program Description:
 * 输入三个整数，输出其中的中位数。
 * 例如 2 8 6 的中位数是 6；三个数相同，中位数就是这个数。
 * 算法：先在前两个数里分出较大的 big 和较小的 small，
 * 再用第三个数去比：比 big 还大就取 big，比 small 还小就取 small，否则取第三个数。
 * 来源：BugZooOrg/IntroClass，匿名提交 000。许可见 INTROCLASS-LICENSE.txt。
 */

#include <iostream>

int main() {
    int num1, num2, num3, median, big, small;

    std::cout << "Please enter 3 numbers separated by spaces > ";
    std::cin >> num1 >> num2 >> num3;

    if (num1 > num2) {
        small = num2;
        big = num1;
    } else {
        big = num2;
        small = num1;
    }
    if (num3 > big)
        median = big;
    else if (num3 < small)
        median = small;
    else
        median = num3;

    std::cout << median << " is the median\n";
    return 0;
}
