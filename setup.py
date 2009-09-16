from distutils.core import setup
setup(name='haikufinder',
      author='Jonathan Feinberg',
      author_email='jdf@pobox.com',
      url='http://mrfeinberg.com/haikufinder/',
      version='1.0',
      packages=['haikufinder'],
      package_dir={'haikufinder':'haikufinder'},
      package_data={'haikufinder': ['cmudict/cmudict.pickle','cmudict/custom.dict']},
      scripts=['scripts/findhaikus'],
      data_files=[('.', ['license.txt'])],
      )
