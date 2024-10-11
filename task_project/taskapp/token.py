from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class CollaboratorTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) +
            str(user.is_collaborator)
        )

collaborator_token = CollaboratorTokenGenerator()