from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from starlette import status

from helpers import paginate
from deps import require_roles, get_db
from models import Role, Author, Book
from schemas import *

router = APIRouter(prefix="/api/books", tags=["books"])

@router.post("/",
             dependencies=[Depends(require_roles(Role.admin))],
             response_model=BookOut,
             status_code=status.HTTP_201_CREATED
             )
def create_book(
        payload:BookCreate,
        db: Session = Depends(get_db),
):
    author = db.query(Author).filter(Author.id == payload.author_id).first()
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Author does not exist"
        )
    book = Book(
        title=payload.title.strip(),
        pages=payload.pages,
        author_id=author.id,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book



@router.get(
    "/",
    response_model= dict,
    status_code=status.HTTP_200_OK,
)
def get_books(
        q:Optional[str] = Query(None,),
        order:str = Query('title'),
        page:int = Query(1, ge=1),
        size:int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
):
    query = db.query(Book).options(joinedload(Book.author))
    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))
    allowed = {'title', 'id'}
    if order.lstrip('-') not in allowed:
        order = 'title'

    col = getattr(Book, order.lstrip('-'))
    if order.startswith('-'):
        col = col.desc()
    query = query.order_by(col)

    data = paginate(query, page=page, size=size)
    data['results'] = [BookOut.model_validate(b) for b in data['results']]
    return data





@router.get(
    "/{book_id}",
    response_model= BookOut ,
    status_code=status.HTTP_200_OK,
)
def get_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    book = db.query(Book).options(joinedload(Book.author)).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} does not exist",
        )
    return book





@router.delete(
    "/{book_id}",
    response_model= BookOut ,
    status_code=status.HTTP_200_OK,
)
def delete_book(
        book_id: int,
        db: Session = Depends(get_db),
):
    book = db.query(Book).options(joinedload(Book.author)).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book {book_id} does not exist",
        )
    db.delete(book)
    db.commit()
    return book 