from typing import Type

import encoders

listen_port = 8123
encoder: Type[encoders.Encoder] = encoders.PickleEncoder

# rules
initial_cash = 1500
initial_field = 0
go_cash = 200
payout_price = 50