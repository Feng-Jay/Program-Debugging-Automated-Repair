/* Program Description:
 * 输入一个名字，在名单里查出这个人的分数。
 * 名单里只有三个人：alice 90，bob 80，cara 70。
 * 找到了就输出“名字 分数”；名单里没有，要输出“找不到”。
 * 算法：用指针 found 指向找到的那一行。没找到时 found 仍是空指针，不能拿去读。
 * 课堂例子：三个已知名字都能查到。下面少了空指针判断，别的名字会直接去读 found。
 */

#include <iostream>
#include <string>

struct Student {
    const char *name;
    int score;
};

int main() {
    Student roster[3] = {
        {"alice", 90},
        {"bob", 80},
        {"cara", 70},
    };
    std::string name;

    std::cout << "请输入名字 > ";
    std::cin >> name;

    const Student *found = nullptr;
    for (int i = 0; i < 3; ++i) {
        if (name == roster[i].name)
            found = &roster[i];
    }

    std::cout << found->name << " " << found->score << "\n";
    return 0;
}
