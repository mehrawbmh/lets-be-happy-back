from bson import ObjectId
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_pascal


class Model(BaseModel):
    model_config = ConfigDict(
        extra='ignore',
        populate_by_name=True,
        use_enum_values=True,
        alias_generator=to_pascal,
        json_schema_extra={},
        json_encoders={ObjectId: str},  # TODO: maybe deprecated in future, find alternative solution
        ser_json_timedelta='float',
        validate_default=True,
        protected_namespaces=('_id',),  # avoid conflict with mongo
    )