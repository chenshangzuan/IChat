"""动态加载 Skills 信息"""
from pathlib import Path
import re


def load_skills(skill_dir: str) -> list[dict]:
    """从目录加载所有 SKILL.md 的信息

    Args:
        skill_dir: skills 目录路径（如 "skills/coder"）

    Returns:
        list of {"name": str, "description": str}
    """
    skills = []
    skill_path = Path(skill_dir)
    if not skill_path.exists():
        return skills

    for skill_folder in skill_path.iterdir():
        if not skill_folder.is_dir():
            continue
        skill_md = skill_folder / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            # 解析 YAML frontmatter
            match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                import yaml
                meta = yaml.safe_load(match.group(1))
                skills.append({
                    "name": meta.get("name", skill_folder.name),
                    "description": meta.get("description", "")
                })
    return skills


def format_skills_list(skills: list[dict]) -> str:
    """格式化技能列表为提示词字符串"""
    if not skills:
        return "无"
    return "\n".join([f"- **{s['name']}**: {s['description']}" for s in skills])


def get_coder_skills() -> list[dict]:
    """获取 Coder Agent 的技能列表"""
    return load_skills("skills/coder")


def get_sre_skills() -> list[dict]:
    """获取 SRE Agent 的技能列表"""
    return load_skills("skills/sre")


if __name__ == "__main__":
    # 测试
    print("Coder Skills:")
    for s in get_coder_skills():
        print(f"  - {s['name']}: {s['description'][:50]}...")

    print("\nSRE Skills:")
    for s in get_sre_skills():
        print(f"  - {s['name']}: {s['description'][:50]}...")
