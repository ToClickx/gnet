import datetime

class DebitCardManager:
    """
    Helper for enforcing debit card limits on spend.
    """

    @staticmethod
    def can_spend(user, card_id, amount) -> bool:
        card = user.debit_cards.get(card_id)
        if not card or not card.get("enabled", False):
            return False

        # Check total spent in time window
        spent = user.get_recent_card_spend(card_id, card.get("time_window_seconds"))
        if spent + amount > card.get("limit_amount", float('inf')):
            return False

        # Check percentage limit relative to gBalance
        if amount > user.gBalance * card.get("limit_percent", 1.0):
            return False

        return True
