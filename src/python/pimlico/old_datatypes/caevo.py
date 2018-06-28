# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from __future__ import absolute_import

from pimlico.old_datatypes.documents import RawDocumentType
from pimlico.old_datatypes.tar import TarredCorpus
from xml.etree import ElementTree as ET


__all__ = ["CaevoCorpus"]


TAG_PREFIX = "{http://chambers.com/corpusinfo}"

def _tag(name):
    return "%s%s" % (TAG_PREFIX, name)


class CaevoDocument(object):
    def __init__(self, name, entries, tlinks):
        self.name = name
        self.entries = entries
        self.tlinks = tlinks

    def __unicode__(self):
        return u"Doc: %s\nEntries:\n%s\nTLinks:\n%s" % (self.name,
                                                        u"\n".join(e.__unicode__(indent=2) for e in self.entries),
                                                        u"\n".join(unicode(t) for t in self.tlinks))

    @staticmethod
    def from_raw_data(raw_data):
        ET.register_namespace("", "")
        xml = ET.fromstring(raw_data.encode("utf-8"))
        # Pull out the doc name from the XML
        name = xml.attrib["name"]
        # Read in sentences from <entry> tags
        entries = [CaevoEntry.from_element(entry) for entry in xml.findall(_tag("entry"))]
        # Build a dictionary of events and timexes as they're referred to in the tlinks
        event_dict = dict(
            [(event.eiid, event) for entry in entries for event in entry.events] +
            [(timex.tid, timex) for entry in entries for timex in entry.timexes]
        )
        # Also read in <tlink> tags
        tlinks = [TLink.from_element(tlink, event_dict) for tlink in xml.findall(_tag("tlink"))]
        return CaevoDocument(name, entries, tlinks)


class CaevoDocumentType(RawDocumentType):
    def process_document(self, doc):
        return CaevoDocument.from_raw_data(doc)


class CaevoCorpus(TarredCorpus):
    """
    Datatype for Caevo output. The output is stored exactly as it comes out from Caevo, in an XML format.
    This datatype reads in that XML and provides easy access to its components.

    Since we simply store the XML that comes from Caevo, there's no corresponding corpus writer. The data is
    output using a :class:pimlico.datatypes.tar.TarredCorpusWriter.

    """
    data_point_type = CaevoDocumentType


class CaevoEntry(object):
    def __init__(self, sid, filename, sentence, tokens, parse=None, deps=None, events=None, timexes=None):
        self.sentence = sentence
        self.tokens = tokens
        self.parse = parse
        self.deps = deps
        self.events = events
        self.timexes = timexes
        self.filename = filename
        self.sid = sid

    @staticmethod
    def from_element(el):
        """ Extract from XML element """
        sentence = el.find(_tag("sentence")).text
        tokens = [_token_to_triple(token.text) for token in el.find(_tag("tokens")).findall(_tag("t"))]
        # Get parse text if there is one
        parse = el.find(_tag("parse"))
        parse = parse.text if parse is not None else None
        # Get dep parse text if there is one
        dep_parse = el.find(_tag("deps"))
        dep_parse = dep_parse.text if dep_parse is not None else None
        # Get any events
        events = [CaevoEvent.from_element(e) for e in el.find(_tag("events")).findall(_tag("event"))]
        # Get any timexes
        timexes = [CaevoTimex.from_element(t) for t in el.find(_tag("timexes")).findall(_tag("timex"))]
        return CaevoEntry(int(el.attrib["sid"]), el.attrib["file"], sentence, tokens, parse, dep_parse, events, timexes)

    def __unicode__(self, indent=0):
        return u"\n".join(u"%s%s" % (u" " * indent, line) for line in [
            u"Entry %d" % self.sid,
            u"  Sentence: %s" % self.sentence,
            u"  Tokens: %s" % self.tokens,
            u"  Parse: %s" % self.parse,
            u"  Dep parse:",
        ] + [
            u"    %s" % line for line in self.deps.splitlines()
        ] + [u"  Events:"] + [
            u"    %s" % event for event in self.events
        ] + [u"  Timexes:"] + [
            u"    %s" % timex for timex in self.timexes
        ])


def _token_to_triple(token_text):
    """
    Split up a token into before text, token text and after text, as it's encoded in Caevo output.

    """
    # Remove outer quotes and any spaces
    token_text = token_text.strip()[1:-1]
    # Text up to first quote-space-quote is the before text
    before_text, __, token_text = token_text.partition('" "')
    # Text up to next quote-space-quote is the actual token text
    # Remaining text is after text
    token, __, after_text = token_text.partition('" "')
    return before_text, token, after_text


class CaevoEvent(object):
    def __init__(self, id, eiid, offset, string, tense, aspect, cls, polarity, modality, happen,
                 lower_bound_duration, upper_bound_duration):
        self.id = id
        self.eiid = eiid
        self.offset = offset
        self.string = string
        self.tense = tense
        self.aspect = aspect
        self.cls = cls
        self.polarity = polarity
        self.modality = modality
        self.happen = happen
        self.lower_bound_duration = lower_bound_duration
        self.upper_bound_duration = upper_bound_duration

    @staticmethod
    def from_element(el):
        d = el.attrib
        return CaevoEvent(
            d["id"], d["eiid"], int(d["offset"]), d["string"], d["tense"], d["aspect"], d["class"], d["polarity"],
            d["modality"], d["happen"], d["lowerBoundDuration"], d["upperBoundDuration"]
        )

    def __unicode__(self):
        return u"Event(id={self.id}, eiid={self.eiid}, '{self.string}')".format(self=self)

    def __repr__(self):
        return unicode(self).encode("ascii", "replace")


class CaevoTimex(object):
    def __init__(self, tid, text, offset, length, type, value, temporal_function):
        self.tid = tid
        self.text = text
        self.offset = offset
        self.length = length
        self.type = type
        self.value = value
        self.temporal_function = temporal_function

    @staticmethod
    def from_element(el):
        d = el.attrib
        return CaevoTimex(
            d["tid"], d["text"], int(d["offset"]), int(d["length"]), d["type"], d["value"], d["temporalFunction"]
        )

    def __unicode__(self):
        return u"Timex(tid={self.tid}, '{self.text}')".format(self=self)


class TLink(object):
    def __init__(self, event1, event2, relation, closed, origin, type, event1_obj=None, event2_obj=None):
        self.event2_obj = event2_obj
        self.event1_obj = event1_obj
        self.event1 = event1
        self.event2 = event2
        self.relation = relation
        self.closed = closed
        self.origin = origin
        self.type = type

    @staticmethod
    def from_element(el, event_dict):
        """ Build from XML element """
        d = el.attrib
        return TLink(
            d["event1"], d["event2"], d["relation"], d["closed"] == "true", d["origin"], d["type"],
            event1_obj=event_dict[d["event1"]], event2_obj=event_dict[d["event2"]],
        )

    def __unicode__(self):
        return u"TLink(e1={self.event1}, e2={self.event2}, {self.relation})".format(self=self)

    def __repr__(self):
        return unicode(self).encode("ascii", "replace")
