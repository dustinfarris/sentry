# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import pickle

from sentry.interfaces import Interface, Message, Query, Stacktrace, get_context
from sentry.models import Event
from sentry.testutils import TestCase, fixture


class InterfaceBase(TestCase):
    @fixture
    def event(self):
        return Event(
            id=1,
        )


class InterfaceTest(InterfaceBase):
    @fixture
    def interface(self):
        return Interface(foo=1)

    def test_init_sets_attrs(self):
        assert self.interface.attrs == ['foo']

    def test_setstate_sets_attrs(self):
        data = pickle.dumps(self.interface)
        obj = pickle.loads(data)
        assert obj.attrs == ['foo']

    def test_to_html_default(self):
        assert self.interface.to_html(self.event) == ''

    def test_to_string_default(self):
        assert self.interface.to_string(self.event) == ''

    def test_get_search_context_default(self):
        assert self.interface.get_search_context(self.event) == {}

    @mock.patch('sentry.interfaces.Interface.get_hash')
    def test_get_composite_hash_calls_get_hash(self, get_hash):
        assert self.interface.get_composite_hash(self.event) == get_hash.return_value
        get_hash.assert_called_once_with()


class MessageTest(InterfaceBase):
    @fixture
    def interface(self):
        return Message(message='Hello there %s!', params=('world',))

    def test_serialize_behavior(self):
        assert self.interface.serialize() == {
            'message': self.interface.message,
            'params': self.interface.params,
        }

    def test_get_hash_uses_message(self):
        assert self.interface.get_hash() == [self.interface.message]

    def test_get_search_context_with_params_as_list(self):
        interface = self.interface
        interface.params = ['world']
        assert interface.get_search_context(self.event) == {
            'text': [interface.message] + list(interface.params)
        }

    def test_get_search_context_with_params_as_tuple(self):
        assert self.interface.get_search_context(self.event) == {
            'text': [self.interface.message] + list(self.interface.params)
        }

    def test_get_search_context_with_params_as_dict(self):
        interface = self.interface
        interface.params = {'who': 'world'}
        interface.message = 'Hello there %(who)s!'
        assert self.interface.get_search_context(self.event) == {
            'text': [interface.message] + interface.params.values()
        }

    def test_get_search_context_with_unsupported_params(self):
        interface = self.interface
        interface.params = object()
        interface.message = 'Hello there %(who)s!'
        assert self.interface.get_search_context(self.event) == {
            'text': [interface.message],
        }


class QueryTest(InterfaceBase):
    @fixture
    def interface(self):
        return Query(query='SELECT 1', engine='psycopg2')

    def test_serialize_behavior(self):
        assert self.interface.serialize() == {
            'query': self.interface.query,
            'engine': self.interface.engine,
        }

    def test_get_hash_uses_query(self):
        assert self.interface.get_hash() == [self.interface.query]

    def test_get_search_context(self):
        assert self.interface.get_search_context(self.event) == {
            'text': [self.interface.query],
        }


class GetContextTest(TestCase):
    def test_works_with_empty_filename(self):
        result = get_context(0, 'hello world')
        assert result == [(0, 'hello world')]
