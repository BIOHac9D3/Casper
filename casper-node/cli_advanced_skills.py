import typer
from core.registry.skills import SkillRegistry

app = typer.Typer()
registry = SkillRegistry()

@app.command()
def discover(domain=None):
    skills = registry.list_all()
    if domain:
        skills = [s for s in skills if s.domain.value == domain.lower()]
    for skill in skills:
        status = 'enabled' if skill.enabled else 'disabled'
        print(f'  {skill.id}: {skill.name} ({skill.domain.value}) - {status}')

@app.command()
def search(query):
    all_skills = registry.list_all()
    results = []
    for skill in all_skills:
        if query.lower() in skill.id.lower() or query.lower() in skill.name.lower():
            results.append(skill)
    for skill in results:
        print(f'  {skill.id}: {skill.name}')

if __name__ == '__main__':
    app()
