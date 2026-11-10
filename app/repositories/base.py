from sqlalchemy.orm import Session
class BaseRepository:
    def __init__(self,db:Session,model): self.db=db; self.model=model
    def get(self,ident): return self.db.get(self.model,ident)
    def list(self,skip=0,limit=100): return self.db.query(self.model).filter(self.model.is_deleted==False).offset(skip).limit(min(limit,200)).all()
