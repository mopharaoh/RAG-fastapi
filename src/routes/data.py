from fastapi import APIRouter,Depends, status, UploadFile, Request
import os
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController,ProjectController, ProcessController
from models import ResponseSignal
from .schemes.data import ProcessRequest 
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemes import DataChunk
import aiofiles
import logging


logger = logging.getLogger('uvicorn.error')
data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"],
)


@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file:UploadFile, # Request is added to access app
                       app_settings: Settings = Depends(get_settings)):
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_prjoct_or_create_one(project_id=project_id)
    data_controller = DataController()
    is_valid, message = data_controller.validate_upload_file(file=file)

    if not is_valid:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                             content={"message": message})
    
    project_controller = ProjectController()
    project_dir_path = project_controller.get_project_path(project_id=project_id)

    file_path, file_id = data_controller.generate_unique_filepath(orig_file_name=file.filename,
                                                          project_id=project_id)

    # Save the uploaded file in chunks to handle large files efficiently
    try:
        async with aiofiles.open(file_path,'wb') as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:
        logger.error(f"Error while uploading file: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                             content={"message": ResponseSignal.FILE_UPLOAD_FAILED.value})
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"message": ResponseSignal.FILE_UPLOAD_SUCCESS.value
                                 , "file_id": file_id,})



@data_router.post("/process/{project_id}")
async def process(request: Request, project_id: str, process_request: ProcessRequest):
    file_id = process_request.file_id
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project = await project_model.get_prjoct_or_create_one(project_id=project_id)
    
    process_controller = ProcessController(project_id=project_id)
    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(file_content=file_content,
                                                     file_id=file_id,
                                                     chunk_size=process_request.chunk_size,
                                                     chunk_overlap=process_request.overlap_size)
    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                             content={"message": ResponseSignal.PROCESSING_FAILED.value})
    file_chunks_records = [
        DataChunk(
            chunk_text=chunk.page_content,
            chunk_metadata=chunk.metadata,
            chunk_order=i+1,
            chunk_project_id=project.id,
        )
        for i, chunk in enumerate(file_chunks)
    ]
    chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)

    if do_reset == 1:
        _ = await chunk_model.delete_chunks_by_project_id(project_id=project.id)
        

    no_records = await chunk_model.insert_many_chunks(chunks=file_chunks_records)

    return JSONResponse({
        "message": ResponseSignal.PROCESSING_SUCCESS.value,
        "Inserted chunks": no_records
    })
