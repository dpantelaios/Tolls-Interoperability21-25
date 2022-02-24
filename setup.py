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
        'pyjwt == 1.6.4',
        'APScheduler',
        'Werkzeug',
        'requests',
        'termcolor'
    ], 
    scripts=[r".\backend\backend.py",r".\api\app.py",r".\cli\cli.py"],
    packages=find_packages(where=r"..\app"),
    entry_points={
        'console_scripts': [
            'se2125=cli:main'
        ]
    }
)
