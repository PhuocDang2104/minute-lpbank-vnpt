import vnpt_audio_pb2 as _vnpt_audio_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RecognizeRequest(_message.Message):
    __slots__ = ("config", "audio")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    AUDIO_FIELD_NUMBER: _ClassVar[int]
    config: RecognitionConfig
    audio: bytes
    def __init__(self, config: _Optional[_Union[RecognitionConfig, _Mapping]] = ..., audio: _Optional[bytes] = ...) -> None: ...

class StreamingRecognizeRequest(_message.Message):
    __slots__ = ("streaming_config", "audio_content")
    STREAMING_CONFIG_FIELD_NUMBER: _ClassVar[int]
    AUDIO_CONTENT_FIELD_NUMBER: _ClassVar[int]
    streaming_config: StreamingRecognitionConfig
    audio_content: bytes
    def __init__(self, streaming_config: _Optional[_Union[StreamingRecognitionConfig, _Mapping]] = ..., audio_content: _Optional[bytes] = ...) -> None: ...

class RecognitionConfig(_message.Message):
    __slots__ = ("encoding", "sample_rate_hertz", "language_code", "max_alternatives", "speech_contexts", "audio_channel_count", "enable_word_time_offsets", "enable_automatic_punctuation", "enable_separate_recognition_per_channel", "model", "verbatim_transcripts", "custom_configuration")
    class CustomConfigurationEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    SAMPLE_RATE_HERTZ_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_CODE_FIELD_NUMBER: _ClassVar[int]
    MAX_ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    SPEECH_CONTEXTS_FIELD_NUMBER: _ClassVar[int]
    AUDIO_CHANNEL_COUNT_FIELD_NUMBER: _ClassVar[int]
    ENABLE_WORD_TIME_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    ENABLE_AUTOMATIC_PUNCTUATION_FIELD_NUMBER: _ClassVar[int]
    ENABLE_SEPARATE_RECOGNITION_PER_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    VERBATIM_TRANSCRIPTS_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    encoding: _vnpt_audio_pb2.AudioEncoding
    sample_rate_hertz: int
    language_code: str
    max_alternatives: int
    speech_contexts: _containers.RepeatedCompositeFieldContainer[SpeechContext]
    audio_channel_count: int
    enable_word_time_offsets: bool
    enable_automatic_punctuation: bool
    enable_separate_recognition_per_channel: bool
    model: str
    verbatim_transcripts: bool
    custom_configuration: _containers.ScalarMap[str, str]
    def __init__(self, encoding: _Optional[_Union[_vnpt_audio_pb2.AudioEncoding, str]] = ..., sample_rate_hertz: _Optional[int] = ..., language_code: _Optional[str] = ..., max_alternatives: _Optional[int] = ..., speech_contexts: _Optional[_Iterable[_Union[SpeechContext, _Mapping]]] = ..., audio_channel_count: _Optional[int] = ..., enable_word_time_offsets: bool = ..., enable_automatic_punctuation: bool = ..., enable_separate_recognition_per_channel: bool = ..., model: _Optional[str] = ..., verbatim_transcripts: bool = ..., custom_configuration: _Optional[_Mapping[str, str]] = ...) -> None: ...

class StreamingRecognitionConfig(_message.Message):
    __slots__ = ("config", "interim_results")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    INTERIM_RESULTS_FIELD_NUMBER: _ClassVar[int]
    config: RecognitionConfig
    interim_results: bool
    def __init__(self, config: _Optional[_Union[RecognitionConfig, _Mapping]] = ..., interim_results: bool = ...) -> None: ...

class SpeechContext(_message.Message):
    __slots__ = ("phrases", "boost")
    PHRASES_FIELD_NUMBER: _ClassVar[int]
    BOOST_FIELD_NUMBER: _ClassVar[int]
    phrases: _containers.RepeatedScalarFieldContainer[str]
    boost: float
    def __init__(self, phrases: _Optional[_Iterable[str]] = ..., boost: _Optional[float] = ...) -> None: ...

class RecognizeResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[SpeechRecognitionResult]
    def __init__(self, results: _Optional[_Iterable[_Union[SpeechRecognitionResult, _Mapping]]] = ...) -> None: ...

class SpeechRecognitionResult(_message.Message):
    __slots__ = ("alternatives", "channel_tag", "audio_processed")
    ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_TAG_FIELD_NUMBER: _ClassVar[int]
    AUDIO_PROCESSED_FIELD_NUMBER: _ClassVar[int]
    alternatives: _containers.RepeatedCompositeFieldContainer[SpeechRecognitionAlternative]
    channel_tag: int
    audio_processed: float
    def __init__(self, alternatives: _Optional[_Iterable[_Union[SpeechRecognitionAlternative, _Mapping]]] = ..., channel_tag: _Optional[int] = ..., audio_processed: _Optional[float] = ...) -> None: ...

class SpeechRecognitionAlternative(_message.Message):
    __slots__ = ("transcript", "confidence", "words")
    TRANSCRIPT_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    WORDS_FIELD_NUMBER: _ClassVar[int]
    transcript: str
    confidence: float
    words: _containers.RepeatedCompositeFieldContainer[WordInfo]
    def __init__(self, transcript: _Optional[str] = ..., confidence: _Optional[float] = ..., words: _Optional[_Iterable[_Union[WordInfo, _Mapping]]] = ...) -> None: ...

class WordInfo(_message.Message):
    __slots__ = ("start_time", "end_time", "word")
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    WORD_FIELD_NUMBER: _ClassVar[int]
    start_time: int
    end_time: int
    word: str
    def __init__(self, start_time: _Optional[int] = ..., end_time: _Optional[int] = ..., word: _Optional[str] = ...) -> None: ...

class StreamingRecognizeResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[StreamingRecognitionResult]
    def __init__(self, results: _Optional[_Iterable[_Union[StreamingRecognitionResult, _Mapping]]] = ...) -> None: ...

class StreamingRecognitionResult(_message.Message):
    __slots__ = ("alternatives", "is_final", "stability", "channel_tag", "audio_processed")
    ALTERNATIVES_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    STABILITY_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_TAG_FIELD_NUMBER: _ClassVar[int]
    AUDIO_PROCESSED_FIELD_NUMBER: _ClassVar[int]
    alternatives: _containers.RepeatedCompositeFieldContainer[SpeechRecognitionAlternative]
    is_final: bool
    stability: float
    channel_tag: int
    audio_processed: float
    def __init__(self, alternatives: _Optional[_Iterable[_Union[SpeechRecognitionAlternative, _Mapping]]] = ..., is_final: bool = ..., stability: _Optional[float] = ..., channel_tag: _Optional[int] = ..., audio_processed: _Optional[float] = ...) -> None: ...
