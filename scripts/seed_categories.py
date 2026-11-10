from app.db.session import SessionLocal, Base, engine
from app.models.models import WasteCategory
Base.metadata.create_all(bind=engine)
db=SessionLocal()
items=[("Organic Waste",False,"Keep separate from dry waste","Compost or approved organic treatment"),("Plastic Waste",True,"Clean and separate by polymer where possible","Send recyclable plastics to an authorized recycler"),("Paper Waste",True,"Keep dry and free of food contamination","Paper recycling"),("Metal Waste",True,"Separate ferrous and non-ferrous metals","Authorized metal recycler"),("Glass Waste",True,"Handle safely; separate broken glass","Glass recycling"),("Electronic Waste",True,"Do not mix with household waste","Authorized e-waste facility"),("Hazardous Waste",False,"Keep isolated and label clearly","Authorized hazardous-waste treatment")]
for name,recyclable,rule,disposal in items:
 if not db.query(WasteCategory).filter_by(name=name).first(): db.add(WasteCategory(name=name,recyclable=recyclable,segregation_rule=rule,disposal_instruction=disposal))
db.commit(); db.close(); print("Default waste categories seeded")
