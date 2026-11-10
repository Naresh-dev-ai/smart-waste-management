from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Any

class ORM(BaseModel): model_config=ConfigDict(from_attributes=True)
class RegisterIn(BaseModel): full_name:str; email:EmailStr; password:str=Field(min_length=8); role:str="customer"; phone:Optional[str]=None
class LoginIn(BaseModel): email:EmailStr; password:str
class RefreshIn(BaseModel): refresh_token:str
class UserOut(ORM): id:int; full_name:str; email:str; role:str; is_active:bool
class ZoneIn(BaseModel): name:str; code:str; description:Optional[str]=None; supervisor_id:Optional[int]=None; schedule:Optional[str]=None
class AreaIn(BaseModel): name:str; locality:str; street:Optional[str]=None; zone_id:int
class CategoryIn(BaseModel): name:str; recyclable:bool=False; segregation_rule:Optional[str]=None; disposal_instruction:Optional[str]=None
class CustomerIn(BaseModel): name:str; phone:str; email:Optional[EmailStr]=None; address:str; area_id:Optional[int]=None; latitude:Optional[float]=None; longitude:Optional[float]=None
class VehicleIn(BaseModel): registration_no:str; vehicle_type:str; capacity_kg:float=Field(gt=0); fuel_type:str
class WorkerIn(BaseModel): name:str; role:str; phone:str; license_no:Optional[str]=None; skills:Optional[str]=None; supervisor_id:Optional[int]=None
class PickupIn(BaseModel): customer_id:int; category_id:int; zone_id:Optional[int]=None; estimated_kg:float=Field(gt=0); pickup_address:str; preferred_date:date; priority:str="normal"; notes:Optional[str]=None
class AssignmentIn(BaseModel): pickup_id:int; vehicle_id:int; driver_id:int; worker_ids:list[int]=[]; scheduled_at:datetime
class CollectionIn(BaseModel): collected_kg:float=Field(gt=0); status:str="completed"; remarks:Optional[str]=None; photo_urls:list[str]=[]
class CenterIn(BaseModel): name:str; address:str; capacity_kg:float=Field(gt=0); accepted_category_ids:list[int]=[]; manager_id:Optional[int]=None
class TransferIn(BaseModel): collection_id:int; center_id:int; vehicle_id:int; category_id:int; quantity_kg:float=Field(gt=0); source_location:str
class SegregationIn(BaseModel): recyclable_kg:float=Field(ge=0); non_recyclable_kg:float=Field(ge=0); contaminated_kg:float=Field(ge=0)
class BatchIn(BaseModel): center_id:int; category_id:int; input_kg:float=Field(gt=0); output_kg:float=Field(ge=0); processing_date:date; status:str="completed"
class DisposalIn(BaseModel): category_id:int; quantity_kg:float=Field(gt=0); method:str; location:str
class MaintenanceIn(BaseModel): vehicle_id:int; description:str; cost:float=Field(ge=0); technician:Optional[str]=None; scheduled_date:Optional[date]=None
class ComplaintIn(BaseModel): customer_id:int; category:str; description:str; priority:str="normal"
