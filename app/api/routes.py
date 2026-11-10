from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.models import *
from app.schemas.schemas import *
from app.core.security import hash_password, verify_password, create_token, decode_token, get_current_user, require_roles
from app.core.audit import audit

router=APIRouter(prefix="/api/v1")
ADMIN=("super_admin",); MANAGERS=("super_admin","operations_manager"); OPS=("super_admin","operations_manager","collection_supervisor")

def active(db, model, ident):
    obj=db.get(model,ident)
    if not obj or getattr(obj,"is_deleted",False): raise HTTPException(404,f"{model.__name__} not found")
    return obj

def create(db, obj, user, action="create"):
    db.add(obj); db.flush(); audit(db,user.id,action,obj.__class__.__name__,obj.id); db.commit(); db.refresh(obj); return obj

@router.post('/auth/register',response_model=UserOut, status_code=201)
def register(data:RegisterIn,db:Session=Depends(get_db)):
    if db.query(User).filter(func.lower(User.email)==data.email.lower()).first(): raise HTTPException(409,"Email already registered")
    if data.role not in {"customer","driver","field_worker","collection_supervisor","operations_manager","recycling_center_manager","super_admin"}: raise HTTPException(422,"Invalid role")
    u=User(full_name=data.full_name,email=data.email.lower(),password_hash=hash_password(data.password),role=data.role,phone=data.phone)
    db.add(u); db.commit(); db.refresh(u); return u
@router.post('/auth/login')
def login(data:LoginIn,db:Session=Depends(get_db)):
    u=db.query(User).filter(func.lower(User.email)==data.email.lower()).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    if not u.is_active: raise HTTPException(403,"Account is inactive")
    audit(db,u.id,"login","User",u.id); db.commit()
    return {"access_token":create_token(str(u.id)),"refresh_token":create_token(str(u.id),"refresh"),"token_type":"bearer"}
@router.post('/auth/refresh')
def refresh(data:RefreshIn,db:Session=Depends(get_db)):
    try:
        p=decode_token(data.refresh_token)
        if p.get('type')!='refresh': raise ValueError()
        u=active(db,User,int(p['sub']))
        if not u.is_active: raise ValueError()
    except Exception: raise HTTPException(401,"Invalid refresh token")
    return {"access_token":create_token(str(u.id)),"refresh_token":create_token(str(u.id),"refresh"),"token_type":"bearer"}
@router.get('/auth/me',response_model=UserOut)
def me(user:User=Depends(get_current_user)): return user
@router.patch('/users/{user_id}/activation')
def activate_user(user_id:int,is_active:bool,db:Session=Depends(get_db),user:User=Depends(require_roles(*ADMIN))):
    u=active(db,User,user_id); u.is_active=is_active; audit(db,user.id,"activation_change","User",u.id,{"is_active":is_active}); db.commit(); return {"id":u.id,"is_active":u.is_active}
@router.post('/auth/password-reset-request')
def password_reset_request(email:EmailStr): return {"message":"If the account exists, follow the password reset instructions. Email delivery must be configured for production."}
@router.post('/auth/password-reset')
def password_reset(user_id:int,new_password:str=Query(min_length=8),db:Session=Depends(get_db),admin:User=Depends(require_roles(*ADMIN))):
    u=active(db,User,user_id); u.password_hash=hash_password(new_password); audit(db,admin.id,"password_reset","User",u.id); db.commit(); return {"message":"Password reset"}

@router.post('/zones',status_code=201)
def zone_create(d:ZoneIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*MANAGERS))):
    return create(db,Zone(**d.model_dump()),u)
@router.get('/zones')
def zones(q:str|None=None,status:str|None=None,skip:int=0,limit:int=100,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=db.query(Zone).filter(Zone.is_deleted==False)
    if q:x=x.filter(Zone.name.ilike(f"%{q}%"))
    if status:x=x.filter(Zone.status==status)
    return x.offset(skip).limit(min(limit,200)).all()
@router.post('/areas',status_code=201)
def area_create(d:AreaIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    active(db,Zone,d.zone_id); return create(db,Area(**d.model_dump()),u)
@router.get('/areas')
def areas(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(Area).filter(Area.is_deleted==False).all()
@router.post('/categories',status_code=201)
def category_create(d:CategoryIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*MANAGERS))): return create(db,WasteCategory(**d.model_dump()),u)
@router.get('/categories')
def categories(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(WasteCategory).filter(WasteCategory.is_deleted==False).all()
@router.post('/customers',status_code=201)
def customer_create(d:CustomerIn,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    if d.area_id: active(db,Area,d.area_id)
    return create(db,Customer(**d.model_dump()),u)
@router.get('/customers')
def customers(q:str|None=None,skip:int=0,limit:int=100,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    x=db.query(Customer).filter(Customer.is_deleted==False)
    if q:x=x.filter((Customer.name.ilike(f"%{q}%"))|(Customer.phone.ilike(f"%{q}%")))
    return x.offset(skip).limit(min(limit,200)).all()

@router.post('/pickups',status_code=201)
def pickup_create(d:PickupIn,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    active(db,Customer,d.customer_id); active(db,WasteCategory,d.category_id)
    if d.zone_id:active(db,Zone,d.zone_id)
    p=create(db,PickupRequest(**d.model_dump()),u,"pickup_created")
    db.add(Notification(title="New pickup request",message=f"Pickup #{p.id} created")); db.commit(); db.refresh(p); return p
@router.get('/pickups')
def pickups(status:str|None=None,zone_id:int|None=None,skip:int=0,limit:int=100,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    x=db.query(PickupRequest).filter(PickupRequest.is_deleted==False)
    if status:x=x.filter(PickupRequest.status==status)
    if zone_id:x=x.filter(PickupRequest.zone_id==zone_id)
    if u.role=="customer":
        c=db.query(Customer).filter(Customer.user_id==u.id).first()
        if c:x=x.filter(PickupRequest.customer_id==c.id)
    return x.order_by(PickupRequest.preferred_date).offset(skip).limit(min(limit,200)).all()
@router.patch('/pickups/{pid}/status')
def pickup_status(pid:int,status:str,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    p=active(db,PickupRequest,pid); allowed={"pending","approved","assigned","scheduled","collected","cancelled","rejected","missed"}
    if status not in allowed: raise HTTPException(422,"Invalid pickup status")
    if status=="cancelled" and p.status in {"collected","rejected"}: raise HTTPException(409,"Cannot cancel completed/rejected pickup")
    if status in {"approved","rejected","assigned","scheduled"} and u.role not in OPS+MANAGERS: raise HTTPException(403,"Supervisor permission required")
    p.status=status; audit(db,u.id,"pickup_status_changed","PickupRequest",pid,{"status":status}); db.commit(); return p

@router.post('/vehicles',status_code=201)
def vehicle_create(d:VehicleIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))): return create(db,Vehicle(**d.model_dump()),u)
@router.get('/vehicles')
def vehicles(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(Vehicle).filter(Vehicle.is_deleted==False).all()
@router.post('/workers',status_code=201)
def worker_create(d:WorkerIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))): return create(db,Worker(**d.model_dump()),u)
@router.get('/workers')
def workers(db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))): return db.query(Worker).filter(Worker.is_deleted==False).all()
@router.post('/assignments',status_code=201)
def assign(d:AssignmentIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    p=active(db,PickupRequest,d.pickup_id); v=active(db,Vehicle,d.vehicle_id); driver=active(db,Worker,d.driver_id)
    if p.status not in {"approved","pending"}: raise HTTPException(409,"Pickup must be pending or approved")
    if v.status!="available": raise HTTPException(409,"Vehicle is not available")
    if v.capacity_kg < p.estimated_kg: raise HTTPException(422,"Vehicle capacity is below estimated waste quantity")
    if not driver.available or driver.role.lower()!="driver": raise HTTPException(409,"Driver is unavailable or not registered as driver")
    for wid in d.worker_ids:
        worker=active(db,Worker,wid)
        if not worker.available: raise HTTPException(409,f"Worker {wid} is unavailable")
    a=Assignment(**d.model_dump()); db.add(a); db.flush(); p.status="assigned"; v.status="assigned"; driver.available=False
    for wid in d.worker_ids: db.get(Worker,wid).available=False
    audit(db,u.id,"assignment_created","Assignment",a.id,{"pickup_id":p.id}); db.commit(); db.refresh(a); return a
@router.post('/collections/{assignment_id}/start')
def start_collection(assignment_id:int,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    a=active(db,Assignment,assignment_id); p=active(db,PickupRequest,a.pickup_id)
    if a.status!="assigned": raise HTTPException(409,"Only assigned collections can be started")
    a.status="in_progress"; p.status="scheduled"; audit(db,u.id,"collection_started","Assignment",a.id); db.commit(); return {"assignment_id":a.id,"status":a.status}

@router.post('/collections/{assignment_id}/complete',status_code=201)
def complete_collection(assignment_id:int,d:CollectionIn,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    a=active(db,Assignment,assignment_id); p=active(db,PickupRequest,a.pickup_id); v=active(db,Vehicle,a.vehicle_id); driver=active(db,Worker,a.driver_id)
    if a.status not in {"assigned","in_progress"}: raise HTTPException(409,"Assignment is not active")
    if d.collected_kg>v.capacity_kg: raise HTTPException(422,"Collected quantity exceeds vehicle capacity")
    if d.status not in {"completed","incomplete","missed"}: raise HTTPException(422,"Collection status must be completed, incomplete or missed")
    c=Collection(pickup_id=p.id,assignment_id=a.id,**d.model_dump()); db.add(c)
    p.status="collected" if d.status=="completed" else ("missed" if d.status=="missed" else "scheduled")
    a.status="completed" if d.status=="completed" else "incomplete"; v.status="available"; driver.available=True
    for wid in a.worker_ids: db.get(Worker,wid).available=True
    audit(db,u.id,"collection_completed","Collection",None,{"pickup_id":p.id,"kg":d.collected_kg,"status":d.status}); db.commit(); db.refresh(c); return c
@router.get('/collections')
def collections(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(Collection).filter(Collection.is_deleted==False).all()

@router.post('/centers',status_code=201)
def center_create(d:CenterIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))): return create(db,RecyclingCenter(**d.model_dump()),u)
@router.get('/centers')
def centers(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(RecyclingCenter).filter(RecyclingCenter.is_deleted==False).all()
@router.post('/transfers',status_code=201)
def transfer_create(d:TransferIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    c=active(db,Collection,d.collection_id); center=active(db,RecyclingCenter,d.center_id); v=active(db,Vehicle,d.vehicle_id)
    if d.quantity_kg>c.collected_kg: raise HTTPException(422,"Transfer quantity exceeds collected quantity")
    if center.status!="active": raise HTTPException(409,"Recycling center is not active")
    if center.accepted_category_ids and d.category_id not in center.accepted_category_ids: raise HTTPException(422,"Center does not accept this category")
    return create(db,Transfer(**d.model_dump()),u)
@router.post('/transfers/{tid}/receive')
def receive_transfer(tid:int,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    t=active(db,Transfer,tid)
    if t.status!="in_transit": raise HTTPException(409,"Transfer is not in transit")
    t.status="received"; audit(db,u.id,"transfer_received","Transfer",tid); db.commit(); return t
@router.post('/segregations',status_code=201)
def segregate(d:SegregationIn,transfer_id:int,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    t=active(db,Transfer,transfer_id)
    if t.status!="received": raise HTTPException(409,"Transfer must be received before segregation")
    if abs(d.recyclable_kg+d.non_recyclable_kg+d.contaminated_kg-t.quantity_kg)>0.001: raise HTTPException(422,"Segregated quantities must equal transfer quantity")
    return create(db,Segregation(transfer_id=transfer_id,**d.model_dump()),u)
@router.post('/processing/batches',status_code=201)
def batch_create(d:BatchIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    active(db,RecyclingCenter,d.center_id); active(db,WasteCategory,d.category_id)
    if d.output_kg>d.input_kg: raise HTTPException(422,"Output cannot exceed input")
    b=ProcessingBatch(loss_kg=round(d.input_kg-d.output_kg,3),**d.model_dump()); return create(db,b,u)
@router.get('/processing/batches')
def batches(db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    return [{"id":b.id,"center_id":b.center_id,"category_id":b.category_id,"input_kg":b.input_kg,"output_kg":b.output_kg,"loss_kg":b.loss_kg,"yield_percent":b.yield_percent,"processing_date":b.processing_date,"status":b.status} for b in db.query(ProcessingBatch).filter(ProcessingBatch.is_deleted==False).all()]
@router.post('/disposals',status_code=201)
def disposal_create(d:DisposalIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    active(db,WasteCategory,d.category_id); return create(db,Disposal(responsible_user_id=u.id,**d.model_dump()),u)
@router.post('/disposals/{did}/approve')
def disposal_approve(did:int,db:Session=Depends(get_db),u:User=Depends(require_roles(*MANAGERS))):
    x=active(db,Disposal,did)
    if x.approved: raise HTTPException(409,"Already approved")
    x.approved=True; x.approved_by_id=u.id; audit(db,u.id,"disposal_approved","Disposal",did); db.commit(); return x

@router.post('/maintenance',status_code=201)
def maintenance_create(d:MaintenanceIn,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    v=active(db,Vehicle,d.vehicle_id); v.status="maintenance"
    return create(db,Maintenance(**d.model_dump()),u)
@router.post('/maintenance/{mid}/complete')
def maintenance_complete(mid:int,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    m=active(db,Maintenance,mid); m.completed=True; db.get(Vehicle,m.vehicle_id).status="available"; audit(db,u.id,"maintenance_completed","Maintenance",mid); db.commit(); return m
@router.post('/complaints',status_code=201)
def complaint_create(d:ComplaintIn,db:Session=Depends(get_db),u:User=Depends(get_current_user)):
    active(db,Customer,d.customer_id); c=create(db,Complaint(**d.model_dump()),u); db.add(Notification(title="New customer complaint",message=f"Complaint #{c.id}")); db.commit(); db.refresh(c); return c
@router.patch('/complaints/{cid}')
def complaint_update(cid:int,status:str,resolution_remarks:str|None=None,assigned_team:str|None=None,db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    c=active(db,Complaint,cid); c.status=status; c.resolution_remarks=resolution_remarks; c.assigned_team=assigned_team; audit(db,u.id,"complaint_updated","Complaint",cid); db.commit(); return c
@router.get('/notifications')
def notifications(db:Session=Depends(get_db),u:User=Depends(get_current_user)): return db.query(Notification).filter((Notification.user_id==None)|(Notification.user_id==u.id)).order_by(Notification.created_at.desc()).all()

@router.get('/reports/dashboard')
def dashboard(db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    count=lambda model: db.query(func.count(model.id)).filter(model.is_deleted==False).scalar() or 0
    total_collected=db.query(func.coalesce(func.sum(Collection.collected_kg),0)).scalar()
    total_recycled=db.query(func.coalesce(func.sum(ProcessingBatch.output_kg),0)).scalar()
    return {"total_customers":count(Customer),"total_collection_requests":count(PickupRequest),"completed_collections":db.query(func.count(Collection.id)).scalar() or 0,"pending_pickups":db.query(func.count(PickupRequest.id)).filter(PickupRequest.status.in_(["pending","approved","assigned","scheduled"])).scalar() or 0,"missed_collections":db.query(func.count(PickupRequest.id)).filter(PickupRequest.status=="missed").scalar() or 0,"total_vehicles":count(Vehicle),"available_vehicles":db.query(func.count(Vehicle.id)).filter(Vehicle.status=="available").scalar() or 0,"active_recycling_centers":db.query(func.count(RecyclingCenter.id)).filter(RecyclingCenter.status=="active").scalar() or 0,"total_waste_collected_kg":float(total_collected),"total_waste_recycled_kg":float(total_recycled),"recycling_efficiency_percent":round(float(total_recycled)/float(total_collected)*100,2) if total_collected else 0,"pending_complaints":db.query(func.count(Complaint.id)).filter(Complaint.status!="resolved").scalar() or 0,"vehicles_in_maintenance":db.query(func.count(Vehicle.id)).filter(Vehicle.status=="maintenance").scalar() or 0}
@router.get('/reports/environmental-impact')
def environmental_impact(db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    collected=float(db.query(func.coalesce(func.sum(Collection.collected_kg),0)).scalar()); recycled=float(db.query(func.coalesce(func.sum(ProcessingBatch.output_kg),0)).scalar()); disposed=float(db.query(func.coalesce(func.sum(Disposal.quantity_kg),0)).filter(Disposal.approved==True).scalar())
    return {"total_waste_collected_kg":collected,"total_waste_recycled_kg":recycled,"total_waste_disposed_kg":disposed,"recycling_percentage_of_collected":round(recycled/collected*100,2) if collected else 0,"assumption":"Recycled quantity is the sum of processing batch output; disposed quantity includes approved disposal records only. Avoid double counting when interpreting these independent totals."}
@router.get('/reports/collections.csv')
def collection_csv(db:Session=Depends(get_db),u:User=Depends(require_roles(*OPS))):
    from fastapi.responses import StreamingResponse
    import csv,io
    rows=db.query(Collection).order_by(Collection.collected_at.desc()).all(); s=io.StringIO(); writer=csv.writer(s); writer.writerow(["id","pickup_id","collected_kg","collected_at","status","remarks"])
    for r in rows: writer.writerow([r.id,r.pickup_id,r.collected_kg,r.collected_at.isoformat(),r.status,r.remarks or ""])
    s.seek(0); return StreamingResponse(iter([s.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=collections.csv"})
@router.get('/audit-logs')
def audit_logs(skip:int=0,limit:int=100,db:Session=Depends(get_db),u:User=Depends(require_roles(*MANAGERS))): return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(min(limit,200)).all()
