from setuptools import setup, find_packages

setup(name='savvy',
      version='0.0.1',
      description='Consolidated assortment of utility modules & classes for savvy Python development.',
      url='https://github.com/whittlbc/savvy',
      author='Ben Whittle',
      author_email='benwhittle31@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_required=[
        'requests==2.18.4'
      ],
      zip_safe=False)