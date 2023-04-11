import inspect
if not hasattr(inspect, 'getargspec'):  # 修复
    inspect.getargspec = inspect.getfullargspec
import sys
from invoke import task
from d2py.tools.write import site

namespace = site('doc', target='doc/_build/html')

@task
def init(ctx):
    ctx.run("pip install sphinx_tabs breathe sphinx-notfound-page west")
    ctx.run("cd doc;make")

namespace.add_task(init)  # 初始化项目
