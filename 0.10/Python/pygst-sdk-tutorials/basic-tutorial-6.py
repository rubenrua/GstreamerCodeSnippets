#!/usr/bin/env python
# -*- coding:utf-8 -*-
# GStreamer SDK Tutorials in Python
#
#     basic-tutorial-6
#
"""
basic-tutorial-6: Media formats and Pad Capabilities
http://docs.gstreamer.com/display/GstSDK/Basic+tutorial+6%3A+Media+formats+and+Pad+Capabilities
"""

import sys
import gst


# Functions below print the Capabilities in a human-friendly format
def print_field(field, value, pfx):
    print "%s  %15s: %s"%(pfx, field, value)
    return True


def print_caps(caps, pfx):
    if caps == None:
        return
    if caps.is_any():
        print "%sANY"%pfx
        return
    if caps.is_empty():
        print "%sEMPTY"%pfx
        return
    for i in xrange(caps.get_size()):
        structure = caps.get_structure(i)
        print "%s%s"% (pfx, structure.get_name())
        structure.foreach(print_field, pfx)


# Prints information about a Pad Template, including its Capabilities
def print_pad_templates_information(factory):
    print "Pad Templates for %s:"% (factory.get_longname())
    if not factory.get_num_pad_templates():
        print "  none"
        return
  
    padstemplates = factory.get_static_pad_templates()
    for padtemplate in padstemplates:
        if padtemplate.direction == gst.PAD_SRC:
            print "  SRC template: '%s'"% padtemplate.name_template
        elif padtemplate.direction == gst.PAD_SINK:
            print "  SINK template: '%s'"% padtemplate.name_template
        else:
            print "  UNKNOWN!!! template: '%s'"% padtemplate.name_template

        if padtemplate.presence == gst.PAD_ALWAYS:
            print "    Availability: Always"
        elif padtemplate.presence == gst.PAD_SOMETIMES:
            print "    Availability: Sometimes"
        elif padtemplatetemplate.presence == gst.PAD_REQUEST:
            print "    Availability: On request"
        else:
            print "    Availability: UNKNOWN!!!"

        if padtemplate.static_caps.string:
            print "    Capabilities:"
            print_caps(padtemplate.get_caps(), "      ") 

        print ""

# Shows the CURRENT capabilities of the requested pad in the given element
def print_pad_capabilities(element, pad_name):

    # Retrieve pad
    pad = element.get_static_pad(pad_name)
    if not pad:
        print >> sys.stderr, "Could not retrieve pad '%s'", pad_name
        return
  
    # Retrieve negotiated caps (or acceptable caps if negotiation is not finished yet)
    caps = pad.get_negotiated_caps()
    if not caps:
        caps = pad.get_caps_reffed()

    # Print and free 
    print "Caps for the %s pad:"% pad_name
    print_caps(caps, "      ")



# Create the element factories
source_factory = gst.element_factory_find("audiotestsrc")
sink_factory = gst.element_factory_find("autoaudiosink")
if not source_factory or not sink_factory:
    print >> sys.stderr, "Not all element factories could be created."
    exit(-1)

# Print information about the pad templates of these factories 
print_pad_templates_information(source_factory)
print_pad_templates_information(sink_factory)

# Ask the factories to instantiate actual elements
source = source_factory.create("source")
sink = sink_factory.create("sink")

# Create the empty pipeline
pipeline = gst.Pipeline("test-pipeline")

if not pipeline or not source or not sink:
    print >> sys.stderr, "Not all elements could be created."
    exit(-1)

# Build the pipeline
pipeline.add(source, sink)
if not gst.element_link_many(source, sink):
    print >> sys.stderr, "Elements could not be linked."
    exit(-1)

# Print initial negotiated caps (in NULL state) 
print "In NULL state:"
print_pad_capabilities(sink, "sink")

# Start playing
ret = pipeline.set_state(gst.STATE_PLAYING)
if ret ==  gst.STATE_CHANGE_FAILURE:
    print >> sys.stderr, "Unable to set the pipeline to the playing state."


# Wait until error, EOS or State Change
bus = pipeline.get_bus()
while True:
    message = bus.timed_pop_filtered(gst.CLOCK_TIME_NONE, gst.MESSAGE_STATE_CHANGED | gst.MESSAGE_ERROR | gst.MESSAGE_EOS)
    if message.type == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print >> sys.stderr, "Error received from element %s: %s"% (message.src.get_name(), err)
        print >> sys.stderr, "Debugging information: %s"% debug
        break
    elif message.type == gst.MESSAGE_EOS:
        print "End-Of-Stream reached."
        break
    elif message.type == gst.MESSAGE_STATE_CHANGED:
        if isinstance(message.src, gst.Pipeline):
            old_state, new_state, pending_state = message.parse_state_changed()
            print ("Pipeline state changed from %s to %s."% 
                   (gst.element_state_get_name(old_state), gst.element_state_get_name (new_state)))
            # Print the current capabilities of the sink element
            print_pad_capabilities (sink, "sink")
    else:
        # We should not reach here because we only asked for ERRORs, EOS and STATE_CHANGED
        print >> sys.stderr, "Unexpected message received."

# Free resources
pipeline.set_state(gst.STATE_NULL)
