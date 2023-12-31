from fastapi import Depends, APIRouter

from app.core.enum.roles import Role
from app.core.enum.tags import Tags
from app.core.enum.task_statuses import TaskStatus
from app.core.services.response_service import responseService
from app.core.services.time_service import TimeService
from app.dependencies.user import get_staff_user, get_admin_user
from app.models.entities.tasks import Task
from app.models.entities.users import User
from app.models.schemas.auth.token_data import UserTokenData
from app.models.schemas.task.task_create import CreateTask
from app.models.schemas.task.task_update import TaskUpdateSchema

router = APIRouter(prefix='/tasks', tags=[Tags.TASK])


@router.post('/')
async def create_task(task_input: CreateTask, user: UserTokenData = Depends(get_staff_user)):
    assignee = await User.find_by_username(task_input.assignee)
    if not assignee:
        return responseService.error_404(f"user with this username: {task_input.assignee} not found.")

    # if (user.role not in AccessLevel.ADMIN.value) and assignee.id != user.id:
    #     raise HTTPException(
    #         status.HTTP_403_FORBIDDEN,
    #         {'message': 'you can not create task for other staff!'}
    #     )

    task = Task.model_validate(
        {
            **task_input.model_dump(),
            'assignee': assignee.username,
            'created_by': user.username
        }
    )

    inserted_task = await task.insert()  # TODO: CRUD handler -> create
    if not inserted_task.acknowledged:
        return responseService.error_500()

    return responseService.success_201(
        {
            'message': 'task created successfully',
            'id': str(inserted_task.inserted_id)
        }
    )


@router.get('/')
async def get_tasks(assigned: bool = True, created_by: bool = True, user: UserTokenData = Depends(get_staff_user)):
    if not (assigned or created_by):
        return responseService.error_400('you have to choose at list one filter')

    first_query = {'assignee': user.username if assigned else False}
    second_query = {'created_by': user.username if created_by else False}
    final_query = {'$or': [first_query, second_query]}

    tasks = await Task.list_find_many(final_query, 20)
    return list(map(
        lambda task: task.model_dump(exclude={'active', 'description', 'finished_at'}),
        tasks
    ))


@router.get('/all')
async def get_all_tasks(user: UserTokenData = Depends(get_admin_user)):
    # TODO: add pagination and filter
    return await Task.list_find_many({}, 100)


@router.get('/{task_id}')
async def get_task_detail(task_id: str, user: UserTokenData = Depends(get_staff_user)):
    task = await Task.find_by_id(task_id, False)
    if user.role == Role.ADMIN or task.assignee == user.username or task.created_by == user.username:
        return task.model_dump()

    return responseService.error_403('You can\'t see this task detail because it is not related to you!')


@router.put('/{task_id}')
async def update_task_detail(update_schema: TaskUpdateSchema, task_id: str,
                             user: UserTokenData = Depends(get_staff_user)):
    existing_task = await Task.find_by_id(task_id, False, 'task not found')
    return responseService.error_501()


@router.patch('/{task_id}')
async def mark_task_done(task_id: str, user: UserTokenData = Depends(get_staff_user)):
    task = await Task.find_by_id(task_id, False, 'task not found')

    if user.role == Role.ADMIN or user.username in (task.assignee, task.created_by):
        task.status = TaskStatus.DONE
        task.active = False
        task.finished_at = TimeService.now()
        result = await task.update()
        return responseService.operation_response(result.acknowledged and result.modified_count)

    return responseService.error_403('you are not allowd to do this action')


@router.delete('/{task_id}')
async def delete_task(task_id: str, just_deactivate: bool = False, user: UserTokenData = Depends(get_staff_user)):
    task = await Task.find_by_id(task_id, False)
    if just_deactivate and not task.active:
        return responseService.error_400('this task is already inactive!')

    if user.role == Role.ADMIN or task.created_by == user.username:
        return responseService.success_204() if await task.delete(just_deactivate) else responseService.error_500()

    return responseService.error_403('only admin or task creator can delete the task!')
