from setuptools import setup,find_packages

setup(
    name='se2125',
    version='1.0.0',
    install_requires=[
        'Flask==2.0.2',
        'Flask-RESTful==0.3.9',
        'mysqlclient==2.1.0',
        'mysql-connector-python==8.0.27',
        'pandas>=1.3.5',
        'jwt',
        'APScheduler',
        'Werkzeug'
        #mysqlcommunity
    ], 
    scripts=[r"..\app\backend.py",r"..\app\app.py",r"..\app\cli.py"],
    packages=find_packages(where=r"..\app"),
    entry_points={
        'console_scripts': [
            'se2125=app.cli:main'
        ]
    }
)