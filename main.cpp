#include <iostream>
#include <string>

void sendLink() {
    std::string link = "https://www.youtube.com/watch?v=3xWJ0FSgJVE";
    std::cout << "Here's our project :) " << link << std::endl;
}

int main() {
    sendLink();
    return 0;
}