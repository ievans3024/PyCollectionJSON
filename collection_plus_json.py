__author__ = 'Ian S. Evans'
__version__ = '0.0.4'

from json import dumps, JSONEncoder, loads
from collections import UserList


class Comparable(object):
    # Stolen shamelessly from Ricardo Kirkner's bindings
    # See https://github.com/ricardokirkner/collection-json.python

    def __init__(self, *args, **kwargs):
        super(Comparable, self).__init__()

    def __eq__(self, other):
        if type(self) == type(other) and self.__dict__ == other.__dict__:
            return True
        return False

    def __ne__(self, other):
        if type(self) != type(other) or self.__dict__ != other.__dict__:
            return True
        return False


class Serializable(object):

    class Encoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, Serializable):
                return o.get_serializable()
            return JSONEncoder.default(self, o)

    def __init__(self, *args, **kwargs):
        super(Serializable, self).__init__()

    def __repr__(self):
        return "<{classname} '{value}'>".format(classname=self.__class__.__name__, value=self.__str__())

    def __str__(self):
        return dumps(self, cls=self.Encoder)

    def get_serializable(self):
        serializable = {}
        for k, v in self.__dict__.items():
            if v:
                if isinstance(v, Serializable):
                    serializable[k] = v.get_serializable()
                else:
                    serializable[k] = v
        return serializable


class Array(Serializable, Comparable, UserList):

    def __init__(self, iterable=[], cls=object, *args, **kwargs):
        super(Array, self).__init__(self, iterable, *args, **kwargs)
        self.required_class = cls
        for item in iterable:
            if isinstance(item, cls):
                self.data.append(item)
            else:
                self.data.append(cls(**item))

    def append(self, item):
        if isinstance(item, self.required_class):
            super(Array, self).append(item)
        else:
            raise TypeError("item must be an instance of {type}".format(type=self.required_class.__name__))

    def get_serializable(self):
        data = []
        for item in self.data:
            if isinstance(item, Serializable):
                data.append(item.get_serializable())
            else:
                data.append(item)
        return data
    
    def __eq__(self, other):
        if type(self) == type(other) and \
                self.required_class == other.required_class and \
                self.data == other.data:
            return True
        return False
    
    def __ne__(self, other):
        if type(self) != type(other) or \
                self.required_class != other.required_class or \
                self.data != other.data:
            return True
        return False


class Collection(Serializable, Comparable):
    """
    { error, href, items, links, queries, template, version }
    """

    __mimetype = "application/vnd.collection+json"

    @property
    def mimetype(self):
        return self.__mimetype

    def __init__(self, href=None, version="1.0", error=None, items=[],
                 links=[], queries=[], template=None, **kwargs):
        super(Collection, self).__init__(self)
        if not kwargs.get("from_json"):
            # Process like normal, apply restrictions to properties
            # from the standard, allow non-standard properties
            self.href = href
            self.version = version

            if error and not isinstance(error, Error):
                error = Error(**error)  # let the class raise exceptions if something's amiss
                self.error = error

            if template and not isinstance(template, Template):
                template = Template(**template)
                self.template = template

            if items and not isinstance(items, Array):
                items = Array(items, cls=Item)
            self.items = items

            if links and not isinstance(links, Array):
                links = Array(links, cls=Link)
            self.links = links

            if queries and not isinstance(queries, Array):
                queries = Array(queries, cls=Query)
            self.queries = queries

            for k, v in kwargs.items():
                # let the user set whatever non-standard data
                # no warranty, express or implied that non-standard
                # data will behave correctly or as expected
                self.__setattr__(k, v)

        else:
            # TODO: allow any kind of TextIO?
            from_json = kwargs.get("from_json")
            if isinstance(from_json, str):
                self.__init__(**loads(kwargs.get("from_json")))

    def __setattr__(self, key, value):

        if key == "error":
            if not isinstance(value, Error):
                value = Error(**value)

        if key == "template":
            if not isinstance(value, Template):
                value = Template(**value)

        if key == "items":
            if not isinstance(value, Array):
                value = Array(value, cls=Item)

        if key == "links":
            if not isinstance(value, Array):
                value = Array(value, cls=Link)

        if key == "queries":
            if not isinstance(value, Array):
                value = Array(value, cls=Query)

        super(Collection, self).__setattr__(key, value)


class Data(Serializable, Comparable):
    """
    { name, prompt, value }
    """
    def __init__(self, name=None, prompt=None, value=None, **kwargs):

        super(Data, self).__init__()

        self.name = name

        if prompt:
            self.prompt = prompt

        if value:
            self.value = value

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Error(Serializable, Comparable):
    """
    { code, message, title }
    """
    def __init__(self, code=None, message=None, title=None, **kwargs):

        super(Error, self).__init__()

        if code:
            self.code = code

        if message:
            self.message = message

        if title:
            self.title = title

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Item(Serializable, Comparable):
    """
    { data, href, links }
    """
    def __init__(self, href=None, data=[], links=[], **kwargs):

        super(Item, self).__init__()

        self.href = href

        if not isinstance(data, Array):
            data = Array(data, cls=Data)
        self.data = data

        if not isinstance(links, Array):
            links = Array(links, cls=Link)
        self.links = links

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Link(Serializable, Comparable):
    """
    { href, name, prompt, rel, render }
    """
    def __init__(self, href=None, rel=None, name=None, prompt=None, render=None, **kwargs):

        super(Link, self).__init__()

        self.href = href
        self.rel = rel

        if name:
            self.name = name

        if prompt:
            self.prompt = prompt

        if render:
            self.render = render

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Query(Serializable, Comparable):
    """
    { data, href, name, prompt, rel }
    """
    def __init__(self, href=None, rel=None, data=None, name=None, prompt=None, **kwargs):

        super(Query, self).__init__()

        self.href = href
        self.rel = rel

        if not isinstance(data, Array):
            data = Array(data, cls=Data)
        self.data = data

        if name:
            self.name = name

        if prompt:
            self.prompt = prompt

        for k, v in kwargs.items():
            self.__setattr__(k, v)


class Template(Serializable, Comparable):
    """
    { data }
    """
    def __init__(self, data=[], **kwargs):

        super(Template, self).__init__()

        if not isinstance(data, Array):
            data = Array(data, cls=Data)
        self.data = data

        for k, v in kwargs.items():
            self.__setattr__(k, v)
