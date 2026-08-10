from decimal import Decimal

from apps.userprofile.wallet_utils import credit_wallet

from .models import ReferralUsage, User

REFERRER_REWARD = Decimal("100.00")
REFERRED_REWARD = Decimal("200.00")


def apply_referral_code(new_user, code):

    code = (code or "").strip().upper()
    if not code:
        return False, ""

    try:
        referrer = User.objects.get(referral_code=code)
    except User.DoesNotExist:
        return False, "Invalid referral code."

    if referrer.id == new_user.id:
        return False, "You cannot use your own referral code."

    if ReferralUsage.objects.filter(referred_user=new_user).exists():
        return False, "Referral already applied for this account."

    ReferralUsage.objects.create(
        referrer=referrer,
        referred_user=new_user,
        referral_code_used=code,
    )

    credit_wallet(
        user=referrer,
        amount=REFERRER_REWARD,
        description=f"Referral bonus — {new_user.full_name} joined using your code",
    )
    credit_wallet(
        user=new_user,
        amount=REFERRED_REWARD,
        description=f"Welcome bonus — signed up using referral code {code}",
    )

    return True, f"Referral applied! You received ₹{REFERRED_REWARD} in your wallet."
