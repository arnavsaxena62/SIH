# client handler
# - class for farmer
# - class for crop
# - api ref for each
# - db to class back to db

from datetime import datetime


class Farmer:
    def __init__(
        self,
        name,
        coordinates,
        contact=None,
        address=None,
        crops=None,
        farmer_id=0
    ):
        self.name = name                     # required
        self.coordinates = coordinates       # required
        self.id = farmer_id                  # default = 0
        self.contact = contact               # optional
        self.address = address               # optional
        self.crops = crops if crops else []  # optional, default empty list


class Crop:
    def __init__(
        self,
        type,
        variety,
        landarea,
        plantingdate,

        # disease classifier
        disease=None,
    ):
        self.type = type
        self.variety = variety
        self.landarea = landarea
        self.plantingdate = datetime.strptime(plantingdate, '%d-%m-%Y')
        self.harvestingdate = self.predictharvest(plantingdate)  # TODO NEED TO MAKE PREDICTHARVEST

        # diseas classifier
        self.disease = disease if disease else []

    def predictharvest(self):
      return 0