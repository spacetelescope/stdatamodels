from pathlib import Path

from .model_base import JwstDataModel


__all__ = ["AsnModel"]


class AsnModel(JwstDataModel):
    """A data model for association tables."""

    schema_url = "http://stsci.edu/schemas/jwst_datamodel/asn.schema"
    supported_formats = ["yaml", "json", "fits"]

    def __init__(self, init=None, **kwargs):
        super(AsnModel, self).__init__(init=init, **kwargs)

        # apply logic to identify output product
        self.parse_table()

    def parse_table(self):
        """Parse the association table to identify the output product and inputs."""
        self.output = None
        self.output_rootname = None
        self.inputs = []
        self.input_rootnames = []
        self.num_inputs = 0

        if not len(self.asn_table):
            return

        for i, etype in enumerate(self.asn_table.exptype):
            if "prod" in etype.lower():
                self.output_rootname = self.asn_table.expname[i]
                for fmt in self.supported_formats:
                    fname = f"{self.output_rootname}.{fmt}"
                    if Path(fname).exists():
                        self.output = fname
                        break
            else:
                rootname = self.asn_table.expname[i]
                for fmt in self.supported_formats:
                    fname = f"{rootname}.{fmt}"
                    if Path(fname).exists():
                        self.inputs.append(fname)
                        break
                self.input_rootnames.append(rootname)
                self.num_inputs += 1
