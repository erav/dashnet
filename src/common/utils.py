
class ToggleStates:
    def __init__(self, number_of_states):
        self._number_of_states = number_of_states
        self._active = 0

    def toggle(self):
        self._active = (self._active + 1) % self._number_of_states

    def toggle_to(self, state):
        self._active = state

    @property
    def active(self):
        return self._active

    def is_active(self, candidate_state):
        return self._active == candidate_state

    def is_not_active(self, candidate_state):
        return not self.is_active(candidate_state)
