Attachment Flags in Trac
========================

The current version works on Trac 1.2. The plugin is developed and maintained
for the `Haiku issue tracker <https://dev.haiku-os.org/>`_.

What is it?
-----------

This plugin adds support for the 'patch' and 'obsolete' attachment flags.
These flags give more control over managing tickets with patches in projects.
For many open source projects, adding patches to tickets is a way to
incorporate contributions from incidental contributors. This plugin helps to
daylight these patches by making them more visible in queries, and to improve
the management when more than one version of the patch is attached.

What is it not?
---------------

* The component only adds the patch and obsolete flags to attachments. It
  does not have flexibility for defining ones own flags like Bugzilla.
* Nor is there support for ticket flags.

The current author does not currently have the intention on adding more
features to the plugin. It will be maintained to work across Trac versions.

Installation
------------

1. Install the module. See the TracPlugins page on
   http://trac.edgewall.org/wiki/TracPlugins.
2. Enable the module. Either use the the Trac admin pages or **add** the 
   following to the ``[components]`` section of the configuration file::

     [components]
     attachmentflags.api.* = enabled
     attachmentflags.web_ui.* = enabled
     
3. Set up a custom ticket field to track whether a ticket has a patch. **Add**
   the following to the ``[ticket-custom]`` section of the configuration file.     
   *You may have to create this section*::

      [ticket-custom]
      patch = checkbox
      patch.label = Has a Patch
      patch.value = 0

4. Upgrade the environment with trac-admin to create the tables in the
   database::
   
     trac-admin /path/to/env upgrade

Using Attachment Flags
----------------------

* There are two attachment flags: one is the patch flag and the other is the
  obsolete flag. Whenever one adds or modifies an attachment, he or she is
  able to set either or both of the flags. 
* If one sets the 'patch' flag, there is a ticket field that will be updated 
  to reflect the fact that there is a patch attached to the ticket. This field 
  is smart: if an attachment is flagged both as patch and as obsolete, then 
  obviously there no longer is a valid patch for that ticket. 
* On the ticket overview pages, it is easy to spot the obsoleted attachements 
  as they are stricken through.
* On the query page it is possible to filter all tickets that have a patch.
