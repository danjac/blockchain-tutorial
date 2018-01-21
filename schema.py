from marshmallow import Schema, fields


class TransactionSchema(Schema):

    sender = fields.String()
    recipient = fields.String()
    amount = fields.Int()


class BlockSchema(Schema):

    index = fields.Int()
    proof = fields.String()
    previous_hash = fields.String()
    timestamp = fields.Float()
    transactions = fields.Nested(TransactionSchema, many=True)


block_schema = BlockSchema()