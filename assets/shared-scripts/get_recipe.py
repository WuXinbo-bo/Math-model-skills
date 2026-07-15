#!/usr/bin/env python3

"""提取指定配方的完整代码。



用法:

  python3 工具/get_recipe.py basic 8        # 提取 basic #8 堆叠面积图

  python3 工具/get_recipe.py competition 16  # 提取 competition #16 网络路径图

  python3 工具/get_recipe.py advanced 1      # 提取 advanced #1 棒棒糖图



输出: 对应配方的完整 markdown 章节（包含代码块和注意事项）

"""

import os, sys, re



RECIPE_FILES = {

    'basic': 'figure_recipes_basic.md',

    'advanced': 'figure_recipes_advanced.md',

    'competition': 'figure_recipes_competition.md',

    'empirical': 'figure_recipes_empirical.md',

    'academic': 'figure_recipes_academic.md',

}



def find_recipe_file(category):

    """在 工具/ 或 skills/shared-scripts/ 中查找配方文件"""

    filename = RECIPE_FILES.get(category.lower())

    if not filename:

        return None

    # 搜索路径：工具/（workspace 运行时）、脚本同目录、skills/shared-scripts/

    script_dir = os.path.dirname(os.path.abspath(__file__))

    for search_dir in ['工具', script_dir, 'skills/shared-scripts', '../skills/shared-scripts']:

        path = os.path.join(search_dir, filename)

        if os.path.isfile(path):

            return path

    return None



def extract_section(content, number):

    """提取 ## N. 开头的完整章节"""

    pattern = re.compile(

        rf'^## {number}\.\s.*?(?=\n## \d+\.|\Z)',

        re.MULTILINE | re.DOTALL

    )

    match = pattern.search(content)

    if match:

        return match.group(0).strip()

    return None



def main():

    if len(sys.argv) < 3:

        print("用法: python3 工具/get_recipe.py <category> <number>")

        print("  category: basic / advanced / competition / empirical")

        print("  number: 配方编号（如 8, 16, 1）")

        print()

        print("示例:")

        print("  python3 工具/get_recipe.py basic 8        # 堆叠面积图")

        print("  python3 工具/get_recipe.py competition 2  # 龙卷风图")

        sys.exit(1)



    category = sys.argv[1].lower()

    number = sys.argv[2]



    if category not in RECIPE_FILES:

        print(f"ERROR: 未知类别 '{category}'，可选: {', '.join(RECIPE_FILES.keys())}")

        sys.exit(1)



    path = find_recipe_file(category)

    if not path:

        print(f"ERROR: 找不到配方文件 {RECIPE_FILES[category]}")

        print("  检查 工具/ 或 skills/shared-scripts/ 目录")

        sys.exit(1)



    with open(path, 'r', encoding='utf-8', errors='replace') as f:

        content = f.read()



    section = extract_section(content, number)

    if not section:

        print(f"ERROR: 在 {RECIPE_FILES[category]} 中找不到 ## {number}. 章节")

        # 列出可用的章节

        headers = re.findall(r'^## (\d+)\.\s+(.+)$', content, re.MULTILINE)

        if headers:

            print(f"\n可用的配方（{category}）:")

            for num, title in headers:

                print(f"  #{num} — {title}")

        sys.exit(1)



    print(section)



if __name__ == '__main__':

    # Windows 控制台 UTF-8 输出

    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    main()

