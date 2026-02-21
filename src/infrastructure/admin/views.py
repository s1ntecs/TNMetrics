from typing import Any

from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, ForeignKeyFilter, OperationColumnFilter

from src.application.security.password import hash_password
from src.infrastructure.db.models import Metric, MetricRecord, Tag, User


class BaseAdmin(ModelView):
    can_view_details = True
    page_size = 50
    page_size_options = [25, 50, 100, 200]


class UserAdmin(BaseAdmin, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [
        User.id,
        User.email,
        User.is_superuser,
        User.is_active,
        User.created_at,
    ]
    column_searchable_list = [User.email]
    column_sortable_list = [User.email, User.is_superuser, User.is_active, User.created_at]
    column_default_sort = [(User.created_at, True)]
    column_filters = [
        BooleanFilter(User.is_superuser, title="Superuser"),
        BooleanFilter(User.is_active, title="Active"),
        OperationColumnFilter(User.email, title="Email"),
    ]
    form_columns = [User.email, User.hashed_password, User.is_superuser, User.is_active]
    form_widget_args = {
        "hashed_password": {
            "placeholder": "Set new password",
            "autocomplete": "new-password",
        }
    }

    async def on_model_change(
        self,
        data: dict[str, Any],
        model: User,
        is_created: bool,
        request: Any,
    ) -> None:
        _ = (model, is_created, request)
        raw_password = str(data.get("hashed_password") or "").strip()

        if not raw_password and not is_created:
            data.pop("hashed_password", None)
            return

        if raw_password and not raw_password.startswith("$"):
            data["hashed_password"] = hash_password(str(raw_password))


class MetricAdmin(BaseAdmin, model=Metric):
    name = "Metric"
    name_plural = "Metrics"
    icon = "fa-solid fa-chart-line"

    column_list = [Metric.id, Metric.user, Metric.name, Metric.description, Metric.created_at]
    column_details_list = [
        Metric.id,
        Metric.user,
        Metric.name,
        Metric.description,
        Metric.created_at,
    ]
    column_searchable_list = [Metric.name, Metric.description]
    column_sortable_list = [Metric.user_id, Metric.name, Metric.created_at]
    column_default_sort = [(Metric.created_at, True)]
    column_filters = [
        ForeignKeyFilter(Metric.user_id, User.email, User, title="Owner"),
        OperationColumnFilter(Metric.name, title="Name"),
    ]
    form_columns = [Metric.user, Metric.name, Metric.description]


class MetricRecordAdmin(BaseAdmin, model=MetricRecord):
    name = "Metric Record"
    name_plural = "Metric Records"
    icon = "fa-solid fa-database"

    column_list = [
        MetricRecord.id,
        MetricRecord.metric,
        MetricRecord.value,
        MetricRecord.timestamp,
        MetricRecord.created_at,
    ]
    column_details_list = [
        MetricRecord.id,
        MetricRecord.metric,
        MetricRecord.value,
        MetricRecord.timestamp,
        MetricRecord.created_at,
        MetricRecord.tags,
    ]
    column_sortable_list = [MetricRecord.value, MetricRecord.timestamp, MetricRecord.created_at]
    column_default_sort = [(MetricRecord.timestamp, True)]
    column_filters = [
        ForeignKeyFilter(MetricRecord.metric_id, Metric.name, Metric, title="Metric"),
        OperationColumnFilter(MetricRecord.value, title="Value"),
    ]
    form_columns = [
        MetricRecord.metric,
        MetricRecord.value,
        MetricRecord.timestamp,
        MetricRecord.tags,
    ]


class TagAdmin(BaseAdmin, model=Tag):
    name = "Tag"
    name_plural = "Tags"
    icon = "fa-solid fa-tag"

    column_list = [Tag.id, Tag.name, Tag.created_at]
    column_searchable_list = [Tag.name]
    column_sortable_list = [Tag.name, Tag.created_at]
    column_default_sort = [(Tag.created_at, True)]
    column_filters = [OperationColumnFilter(Tag.name, title="Name")]
    form_columns = [Tag.name]
