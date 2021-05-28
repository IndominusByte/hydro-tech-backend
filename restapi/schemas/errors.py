from pydantic import PydanticValueError

# ========= USER SECTION =========

class PhoneNumberError(PydanticValueError):
    code = 'phone_number'
    msg_template = 'value is not a valid mobile phone number'

class PasswordConfirmError(PydanticValueError):
    code = 'password_confirm'
    msg_template = 'password must match with password confirmation'
