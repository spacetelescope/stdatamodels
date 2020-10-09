"""
Proof of concept of using tags with the data model framework
"""

from asdf.extension import Converter

class Bozo:
	def __init__(self, clown_cert, clown_school):
		self.clown_cert = clown_cert
		self.clown_school = clown_school
		self._tag = "tag:stsci.edu:datamodels/bozo-1.0.0"

class BozoConverter(Converter):

	tags = [
        "tag:stsci.edu:datamodels/bozo-*"
	]
	types = ["stdatamodels.bozo.Bozo"]
	#types = ["stdatamodels.typed_nodes.Bozo"]

	def to_yaml_tree(self, obj, tags, ctx): 
		retval = {
			'clown_cert': 'expert',
			'clown_school': 'creepy'
		}
		return retval

	def from_yaml_tree(self, node, tag, ctx):
		return Bozo(node['clown_cert'], node['clown_school'])
	    