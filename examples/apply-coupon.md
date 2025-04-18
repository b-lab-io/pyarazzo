# apply-coupon

This is how you can find a pet, find an applicable coupon, and apply that coupon in your order. The workflow concludes by outputting the ID of the placed order.

## Workflow Diagram

```plantuml
@startuml
skinparam backgroundColor #EEEBDC
skinparam handwritten true

participant "apply-coupon" as apply_coupon
participant "find-pet" as find_pet
participant "find-coupons" as find_coupons
participant "place-order" as place_order
apply_coupon --> find_pet : None
apply_coupon --> find_coupons : Find a coupon available for the selected pet.
apply_coupon --> place_order : None
@enduml
```

## Steps

### find-pet

**ID**: find-pet

None

### find-coupons

**ID**: find-coupons

Find a coupon available for the selected pet.

### place-order

**ID**: place-order

None

