import pytest

from ldotel.tracing import Hook, HookOptions

from ldclient import Config, LDClient, Context
from ldclient.integrations.test_data import TestData

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter, SpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace import Tracer, TracerProvider
from opentelemetry.trace import set_tracer_provider, get_tracer_provider


@pytest.fixture
def td() -> TestData:
    td = TestData.data_source()
    td.update(td.flag('boolean').variation_for_all(True))

    return td


@pytest.fixture
def exporter() -> SpanExporter:
    return InMemorySpanExporter()


@pytest.fixture
def tracer(exporter: SpanExporter) -> Tracer:
    set_tracer_provider(TracerProvider())
    get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))

    return get_tracer_provider().get_tracer('pytest')


@pytest.fixture
def client(td: TestData) -> LDClient:
    config = Config('sdk-key', update_processor_class=td, send_events=False)

    return LDClient(config=config)


class TestHookOptions:
    def test_does_nothing_if_not_in_span(self, client: LDClient, exporter: SpanExporter):
        client.add_hook(Hook())
        client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 0

    def test_records_basic_span_event(self, client: LDClient, exporter: SpanExporter, tracer: Tracer):
        client.add_hook(Hook())
        with tracer.start_as_current_span("test_records_basic_span_event"):
            client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert len(spans[0].events) == 1

        event = spans[0].events[0]
        assert event.name == 'feature_flag'
        assert event.attributes['feature_flag.key'] == 'boolean'
        assert event.attributes['feature_flag.provider_name'] == 'LaunchDarkly'
        assert event.attributes['feature_flag.context.key'] == 'org:org-key'
        assert 'feature_flag.variant' not in event.attributes

    def test_can_include_variant(self, client: LDClient, exporter: SpanExporter, tracer: Tracer):
        client.add_hook(Hook(HookOptions(include_variant=True)))
        with tracer.start_as_current_span("test_can_include_variant"):
            client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 1
        assert len(spans[0].events) == 1

        event = spans[0].events[0]
        assert event.name == 'feature_flag'
        assert event.attributes['feature_flag.key'] == 'boolean'
        assert event.attributes['feature_flag.provider_name'] == 'LaunchDarkly'
        assert event.attributes['feature_flag.context.key'] == 'org:org-key'
        assert event.attributes['feature_flag.variant'] == 'True'

    def test_add_span_creates_span_if_one_not_active(self, client: LDClient, exporter: SpanExporter, tracer: Tracer):
        client.add_hook(Hook(HookOptions(add_spans=True)))
        client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 1

        assert spans[0].attributes['feature_flag.context.key'] == 'org:org-key'
        assert spans[0].attributes['feature_flag.key'] == 'boolean'
        assert len(spans[0].events) == 0

    def test_add_span_leaves_events_on_top_level_span(self, client: LDClient, exporter: SpanExporter, tracer: Tracer):
        client.add_hook(Hook(HookOptions(add_spans=True)))
        with tracer.start_as_current_span("test_add_span_leaves_events_on_top_level_span"):
            client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 2

        ld_span = spans[0]
        toplevel = spans[1]

        assert ld_span.attributes['feature_flag.context.key'] == 'org:org-key'
        assert ld_span.attributes['feature_flag.key'] == 'boolean'

        event = toplevel.events[0]
        assert event.name == 'feature_flag'
        assert event.attributes['feature_flag.key'] == 'boolean'
        assert event.attributes['feature_flag.provider_name'] == 'LaunchDarkly'
        assert event.attributes['feature_flag.context.key'] == 'org:org-key'
        assert 'feature_flag.variant' not in event.attributes

    def test_hook_makes_its_span_active(self, client: LDClient, exporter: SpanExporter, tracer: Tracer):
        client.add_hook(Hook(HookOptions(add_spans=True)))
        client.add_hook(Hook(HookOptions(add_spans=True)))

        with tracer.start_as_current_span("test_add_span_leaves_events_on_top_level_span"):
            client.variation('boolean', Context.create('org-key', 'org'), False)

        spans = exporter.get_finished_spans()
        assert len(spans) == 3

        inner = spans[0]
        middle = spans[1]
        top = spans[2]

        assert inner.attributes['feature_flag.context.key'] == 'org:org-key'
        assert inner.attributes['feature_flag.key'] == 'boolean'
        assert len(inner.events) == 0

        assert middle.attributes['feature_flag.context.key'] == 'org:org-key'
        assert middle.attributes['feature_flag.key'] == 'boolean'
        assert middle.events[0].name == 'feature_flag'
        assert middle.events[0].attributes['feature_flag.key'] == 'boolean'
        assert middle.events[0].attributes['feature_flag.provider_name'] == 'LaunchDarkly'
        assert middle.events[0].attributes['feature_flag.context.key'] == 'org:org-key'
        assert 'feature_flag.variant' not in middle.events[0].attributes

        assert top.events[0].name == 'feature_flag'
        assert top.events[0].attributes['feature_flag.key'] == 'boolean'
        assert top.events[0].attributes['feature_flag.provider_name'] == 'LaunchDarkly'
        assert top.events[0].attributes['feature_flag.context.key'] == 'org:org-key'
        assert 'feature_flag.variant' not in top.events[0].attributes
