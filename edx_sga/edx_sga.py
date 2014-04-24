"""
This block defines a Staff Graded Assignment.  Students are shown a rubric
and invited to upload a file which is then graded by staff.
"""
import logging
import pkg_resources

from django.conf import settings
from django.template.context import Context
from django.template.loader import get_template

from webob.response import Response

from xblock.core import XBlock
from xblock.fields import Scope, String, Float
from xblock.fragment import Fragment

log = logging.getLogger(__name__)


class StaffGradedAssignmentXBlock(XBlock):
    """
    This block defines a Staff Graded Assignment.  Students are shown a rubric
    and invited to upload a file which is then graded by staff.
    """
    has_score = True
    icon_class = 'problem'

    display_name = String(
        default='Staff Graded Assignment', scope=Scope.settings,
        help="This name appears in the horizontal navigation at the top of "
             "the page.")

    weight = Float(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": .1},
        scope=Scope.settings
    )

    points = Float(
        display_name="Maximum score",
        help=("Maximum grade score given to assignment by staff."),
        values={"min": 0, "step": .1},
        default=100,
        scope=Scope.settings
    )

    score = Float(
        display_name="Grade score",
        default=0,
        help=("Grade score given to assignment by staff."),
        values={"min": 0, "step": .1},
        scope=Scope.user_state
    )

    uploaded_sha1 = String(
        display_name="Upload SHA1",
        scope=Scope.user_state,
        default=None,
        help="sha1 of the file uploaded by the student for this assignment.")

    uploaded_filename = String(
        display_name="Upload file name",
        scope=Scope.user_state,
        default=None,
        help="The name of the file uploaded for this assignment.")

    def max_score(self):
        return self.points

    def student_view(self, context=None):
        """
        The primary view of the StaffGradedAssignmentXBlock, shown to students
        when viewing courses.
        """
        template = get_template("staff_graded_assignment/show.html")
        fragment = Fragment(template.render(Context({})))
        fragment.add_css(_resource("static/css/edx_sga.css"))
        fragment.add_javascript(_resource("static/js/src/edx_sga.js"))
        fragment.initialize_js('StaffGradedAssignmentXBlock')
        return fragment

    def studio_view(self, context=None):
        try:
            cls = type(self)
            def none_to_empty(x):
                return x if x is not None else ''
            edit_fields = (
                (field, none_to_empty(getattr(self, field.name)), validator)
                for field, validator in (
                    (cls.display_name, 'string'),
                    (cls.points, 'number'),
                    (cls.weight, 'number')))

            template = get_template("staff_graded_assignment/edit.html")
            fragment = Fragment(template.render(Context({
                "fields": edit_fields
            })))
            fragment.add_javascript(_resource("static/js/src/studio.js"))
            fragment.initialize_js('StaffGradedAssignmentXBlock')
            return fragment
        except:
            log.error("Don't swallow my exceptions", exc_info=True)
            raise

    @XBlock.json_handler
    def save_sga(self, data, suffix=''):
        for name in ('display_name', 'points', 'weight'):
            setattr(self, name, data.get(name, getattr(self, name)))

    @XBlock.handler
    def upload_assignment(self, request, suffix=''):
        blobs = settings.BLOB_STORAGE()
        upload = request.params['assignment']
        prev = self.uploaded_sha1
        self.uploaded_sha1 = blobs.store(upload.file)
        self.uploaded_filename = upload.file.name
        if prev:
            blobs.remove(prev)
        return Response(json_body="OK")


def _resource(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")
