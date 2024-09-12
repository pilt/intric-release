import base64
import json

from openai import AsyncOpenAI

from instorage.ai_models.completion_models import get_response_open_ai
from instorage.ai_models.completion_models.completion_model import (
    CompletionModel,
    Context,
    ModelKwargs,
)
from instorage.files.file_models import File
from instorage.logging.logging import LoggingDetails
from instorage.main.config import get_settings
from instorage.main.logging import get_logger

logger = get_logger(__name__)


TOKENS_RESERVED_FOR_COMPLETION = 1000


class OpenAIModelAdapter:
    def __init__(
        self,
        model: CompletionModel,
        client: AsyncOpenAI = AsyncOpenAI(api_key=get_settings().openai_api_key),
    ):
        self.model = model
        self.client = client

    def _get_kwargs(self, kwargs: ModelKwargs | None):
        if kwargs is None:
            return {}

        return kwargs.model_dump(exclude_none=True)

    def get_token_limit_of_model(self):
        return self.model.token_limit - TOKENS_RESERVED_FOR_COMPLETION

    def get_logging_details(self, context: Context, model_kwargs: ModelKwargs):
        query = self.create_query_from_context(context=context)
        return LoggingDetails(
            json_body=json.dumps(query), model_kwargs=self._get_kwargs(model_kwargs)
        )

    def _build_image(self, file: File):
        image_data = base64.b64encode(file.image).decode("utf-8")

        return {
            "type": "image_url",
            "image_url": {"url": f"data:{file.mimetype};base64,{image_data}"},
        }

    def _build_content(
        self,
        input: str,
        images: list[File],
    ):
        content = [
            {
                "type": "text",
                "text": input,
            }
        ]

        for image in images:
            content.append(self._build_image(image))

        return content

    def create_query_from_context(self, context: Context):
        system_message = [{"role": "system", "content": context.prompt}]

        previous_messages = [
            message
            for question in context.messages
            for message in [
                {
                    "role": "user",
                    "content": self._build_content(
                        input=question.question,
                        images=question.images,
                    ),
                },
                {"role": "assistant", "content": question.answer},
            ]
        ]
        question = [
            {
                "role": "user",
                "content": self._build_content(
                    input=context.input,
                    images=context.images,
                ),
            }
        ]

        return system_message + previous_messages + question

    async def get_response(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        query = self.create_query_from_context(context=context)
        return await get_response_open_ai.get_response(
            client=self.client,
            model_name=self.model.name,
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
        )

    def get_response_streaming(
        self,
        context: Context,
        model_kwargs: ModelKwargs | None = None,
    ):
        query = self.create_query_from_context(context=context)
        return get_response_open_ai.get_response_streaming(
            client=self.client,
            model_name=self.model.name,
            messages=query,
            model_kwargs=self._get_kwargs(model_kwargs),
        )