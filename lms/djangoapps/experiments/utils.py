from student.models import CourseEnrollment
from django_comment_common.models import Role
from courseware.access import has_staff_access_to_preview_mode
from course_modes.models import (
    get_cosmetic_verified_display_price
)
from courseware.date_summary import (
    verified_upgrade_deadline_link, verified_upgrade_link_is_valid
)
from xmodule.partitions.partitions_service import get_user_partition_groups, get_all_partitions_for_course
from crum import get_current_request
from openedx.core.djangoapps.programs.utils import ProgramDataExtender, ProgramProgressMeter


def check_and_get_upgrade_link_and_date(user, enrollment=None, course=None):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.

    Returns the upgrade link and upgrade deadline for a user in a given course given
    that the user is within the window to upgrade defined by our dynamic pacing feature;
    otherwise, returns None for both the link and date.
    """
    if enrollment is None and course is None:
        raise ValueError("Must specify either an enrollment or a course")

    if enrollment:
        if course is None:
            course = enrollment.course
        elif enrollment.course_id != course.id:
            raise ValueError("{} refers to a different course than {} which was supplied".format(
                enrollment, course
            ))

        if enrollment.user_id != user.id:
            raise ValueError("{} refers to a different user than {} which was supplied".format(
                enrollment, user
            ))

    if enrollment is None:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)

    if user.is_authenticated and verified_upgrade_link_is_valid(enrollment):
        return (
            verified_upgrade_deadline_link(user, course),
            enrollment.upgrade_deadline
        )

    return (None, None)


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    enrollment_mode = None
    enrollment_time = None
    enrollment = None
    # TODO: clean up as part of REVO-28 (START)
    has_non_audit_enrollments = None
    # TODO: clean up as part of REVO-28 (END)
    # TODO: clean up as part of REVEM-106 (START)
    program_key = None
    # TODO: clean up as part of REVEM-106 (END)
    try:
        # TODO: clean up as part of REVO-28 (START)
        user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
        audit_enrollments = user_enrollments.filter(mode='audit')
        has_non_audit_enrollments = (len(audit_enrollments) != len(user_enrollments))
        # TODO: clean up as part of REVO-28 (END)
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created

            # TODO: clean up as part of REVEM-106 (START)
            # get program data for this course
            request = get_current_request()
            if request:
                enrollment_list = [enrollment]
                meter = ProgramProgressMeter(request.site, user, enrollments=enrollment_list)
                if meter.engaged_programs and meter.engaged_programs[0]:
                    org_name = None
                    courses_not_started = 0
                    courses_in_progress = 0
                    courses_completed = 0
                    program_data = meter.engaged_programs[0]
                    program_data = ProgramDataExtender(program_data, user, mobile_only=False).extend()
                    program_orgs = program_data.get('credit_backing_organizations')
                    if program_orgs and program_orgs[0]:
                        org = program_orgs[0]
                        org_name = org.get('name')
                    if meter.progress() and meter.progress()[0]:
                        progress = meter.progress()[0]
                        courses_not_started = progress.get('not_started')
                        courses_in_progress = progress.get('in_progress')
                        courses_completed = progress.get('completed')
                    program_key = {
                        'uuid': program_data.get('uuid'),
                        'title': program_data.get('title'),
                        'marketing_url': program_data.get('marketing_url'),
                        'org_name': org_name,
                        'courses_not_started': courses_not_started,
                        'courses_in_progress': courses_in_progress,
                        'courses_completed': courses_completed,
                    }
            # TODO: clean up as part of REVEM-106 (END)
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, used the default None values

    # upgrade_link and upgrade_date should be None if user has passed their dynamic pacing deadline.
    upgrade_link, upgrade_date = check_and_get_upgrade_link_and_date(user, enrollment, course)
    has_staff_access = has_staff_access_to_preview_mode(user, course.id)
    forum_roles = []
    if user.is_authenticated:
        forum_roles = list(Role.objects.filter(users=user, course_id=course.id).values_list('name').distinct())

    # get user partition data
    if user.is_authenticated():
        partition_groups = get_all_partitions_for_course(course)
        user_partitions = get_user_partition_groups(course.id, partition_groups, user, 'name')
    else:
        user_partitions = {}

    return {
        'upgrade_link': upgrade_link,
        'upgrade_price': unicode(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
        'has_staff_access': has_staff_access,
        'forum_roles': forum_roles,
        'partition_groups': user_partitions,
        # TODO: clean up as part of REVO-28 (START)
        'has_non_audit_enrollments': has_non_audit_enrollments,
        # TODO: clean up as part of REVO-28 (END)
        # TODO: clean up as part of REVEM-106 (START)
        'program_key_fields': program_key,
        # TODO: clean up as part of REVEM-106 (END)
    }
