# UPI Fraud Typologies — Full Specification

> Each typology below includes: description, attacker MO, victim profile, synthetic signals (features the generator injects), parameters, and detection hints.

---

## 1. Fake Collect Request

**Description:** The victim receives a UPI "collect request" (a pull payment request) from a fraudster. The request message claims it is a refund, cashback, or prize. The victim, misunderstanding that approving a collect request sends money rather than receiving it, enters their PIN and authorises the payment.

**Attacker MO:**
- Fraudster obtains victim's VPA from social media, classifieds (OLX, Quikr), or by posing as a buyer.
- Sends a collect request with a deceptive note ("Refund of ₹2,999", "Cashback credited — approve to receive").
- Amount is typically ₹1,000–₹10,000, sometimes repeated in rapid succession.

**Victim Profile:**
- First-time or infrequent UPI users, senior citizens, small sellers on classifieds.
- Low transaction velocity, few unique payees.

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `is_collect_request` | True |
| `payee_first_seen_days` | 0 (brand new payee) |
| `amount_z_score` | Moderate-to-high (unusual amount for user) |
| `user_txn_velocity_1h` | Low (victim is not a power user) |
| `recipient_account_age_days` | < 30 (freshly created mule VPA) |

**Parameters:**
- Amount range: ₹500–₹9,999
- Collect note keywords: "refund", "cashback", "prize"
- Victim selection: users with < 20 lifetime transactions

**Detection Hints:**
- Collect request + new payee + recipient is young account → high risk.
- Multiple collect requests from same recipient within minutes → amplifier.

---

## 2. Impersonation / Vishing

**Description:** Fraudster calls the victim posing as a bank official, RBI officer, or government agent. During or shortly after the call, the victim is coerced into making a large UPI transfer to a "verification account" or "safe account."

**Attacker MO:**
- Caller ID spoofing to show bank helpline number.
- Induces urgency ("your account will be frozen in 30 minutes").
- Victim makes a push payment to a mule VPA while still on the call or within minutes.

**Victim Profile:**
- Senior citizens, salaried individuals, people who recently reported a banking issue.
- Higher balances, infrequent large transfers.

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `call_active_flag` | True (simulated: call in progress or ended < 5 min ago) |
| `payee_first_seen_days` | 0 |
| `amount_z_score` | Very high (often > 3σ) |
| `amount_ratio_to_max` | > 0.8 |
| `hour_deviation` | Possibly unusual (off-hours calls) |
| `recipient_account_age_days` | < 60 |

**Parameters:**
- Amount range: ₹10,000–₹100,000
- Call flag window: payment within 10 minutes of simulated call
- Victim selection: users with balance > ₹50,000, age > 50

**Detection Hints:**
- Call-active flag + large amount + new payee → very high risk.
- Recipient account being young and receiving from multiple victims → mule signal.

---

## 3. QR Code Swap

**Description:** At a physical merchant location (tea stall, petrol pump, small shop), a fraudster replaces the merchant's QR code with their own. The customer scans the swapped QR and pays the fraudster instead of the merchant.

**Attacker MO:**
- Physically pastes a different QR sticker over the merchant's real one.
- The swapped VPA is typically a mule account, not the expected merchant VPA.
- Amounts are small to medium (typical purchase amounts).

**Victim Profile:**
- Regular shoppers, not necessarily vulnerable — anyone can scan a swapped QR.
- The merchant is also a victim (doesn't receive payment).

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `payee_vpa_matches_merchant_history` | False (user has paid this merchant before, but VPA differs) |
| `payee_first_seen_days` | 0 (new VPA, but same "merchant location") |
| `is_merchant_txn` | True (user's pattern suggests merchant payment) |
| `amount_z_score` | Low (normal purchase amount) |
| `recipient_fan_in_1h` | High (many customers paying the swapped QR) |

**Parameters:**
- Amount range: ₹50–₹2,000
- Simulated via: user has a regular merchant payee; fraud transaction goes to a different VPA with same "merchant_label"
- Fan-in on the mule QR account: 5–20 payments from different payers within hours

**Detection Hints:**
- Payee VPA mismatch with merchant history.
- High fan-in to a new account from geographically similar users.
- Individual transaction looks benign; network pattern is the key signal.

---

## 4. Rapid New-Payee Burst (Money Mule Loading)

**Description:** A compromised or coerced account suddenly makes many small-to-medium transfers to new payees in rapid succession. This is the "loading" phase where stolen funds are distributed to multiple mule accounts.

**Attacker MO:**
- Account is compromised via phishing or SIM swap.
- Automated or semi-automated transfers to 5–15 new payees within 10–30 minutes.
- Amounts are varied to avoid round-number detection.

**Victim Profile:**
- The account holder whose credentials are stolen. Typically has a healthy balance.
- May not be aware until they check their statement.

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `user_txn_velocity_1min` | Very high (> 3 txns/min) |
| `user_txn_velocity_1h` | Very high (> 10 txns/hr, when normal is 1–2) |
| `new_payee_count_1h` | Very high (> 5 new payees) |
| `amount_z_score` | Variable (amounts chosen to be plausible) |
| `payee_first_seen_days` | 0 for all payees |

**Parameters:**
- Number of transfers: 5–15 in a burst
- Time window: 5–30 minutes
- Amount per transfer: ₹1,000–₹15,000
- All payees are new to the sender

**Detection Hints:**
- Velocity spike + all-new-payees → very high risk.
- Downstream accounts may show similar rapid forwarding (mule chain signal).

---

## 5. Mule Chain Layering (A→B→C→D)

**Description:** Stolen funds move through a chain of mule accounts (A→B→C→D) within minutes. Each hop is designed to launder the money trail. Mule accounts are typically young, have high pass-through ratios, and short fund dwell times.

**Attacker MO:**
- Recruit or create a network of mule accounts (often using stolen IDs).
- Move money from victim → mule1 → mule2 → mule3 in rapid succession (each hop within 1–5 minutes).
- Final mule may withdraw cash or transfer to a different payment rail.

**Victim Profile:**
- Victim initiates the first transfer (via any of the above scams).
- Mule accounts are the detection target here.

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `account_age_days` | < 30 for mule accounts |
| `pass_through_ratio` | > 0.8 (most inbound funds are forwarded out quickly) |
| `fund_dwell_time_seconds` | < 300 (money leaves within minutes) |
| `fan_in_fan_out_ratio` | Close to 1.0 (acts as a pass-through) |
| `distinct_senders_1h` | Moderate (receives from a few victims/mules) |
| `distinct_receivers_1h` | Moderate (forwards to next layer) |
| `hop_distance_to_flagged` | Small (connected to other suspicious accounts) |

**Parameters:**
- Chain length: 3–5 hops
- Dwell time per hop: 30 seconds–5 minutes
- Mule account age: 1–30 days
- Pass-through ratio: > 0.85
- Number of chains generated: configurable

**Detection Hints:**
- Young account + high pass-through + short dwell → mule score.
- Connected component of young, high-pass-through accounts → mule network.
- Temporal pattern: inbound followed by near-equal outbound within minutes.

---

## 6. Remote Access / Screen-Share Scam

**Description:** Fraudster convinces victim to install a remote-access app (AnyDesk, TeamViewer, QuickSupport). While screen-sharing is active, the fraudster either directly initiates a UPI payment or guides the victim through it.

**Attacker MO:**
- Poses as tech support, bank helpline, or e-commerce support.
- Convinces victim to install remote-access software and share the access code.
- Initiates transfers while screen is shared, or instructs the victim to do so.

**Victim Profile:**
- Non-tech-savvy users, senior citizens, people with recent complaints on social media.
- Often panicked by a fake "security alert."

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `screen_share_active` | True |
| `new_device_flag` | True (remote session may appear as new device) |
| `payee_first_seen_days` | 0 |
| `amount_z_score` | High |
| `call_active_flag` | Often True (concurrent with screen share) |
| `user_txn_velocity_1h` | Low (victim is not usually active) |

**Parameters:**
- Screen-share flag: True during the fraud window
- Often combined with call-active flag
- Amount range: ₹5,000–₹50,000
- New device fingerprint injected

**Detection Hints:**
- Screen-share active + new device + new payee + high amount → critical risk.
- Combination of screen-share and call flags is rare in genuine transactions.

---

## 7. Account Takeover (New Device + New City + SIM Swap)

**Description:** Fraudster gains control of victim's account, typically through SIM swap, and logs in from a new device in a different city. They then drain the account via transfers to mule accounts.

**Attacker MO:**
- SIM swap: fraudster convinces telecom to port victim's number, gaining OTP access.
- Logs into UPI app from a new device, often in a different city.
- Makes multiple transfers to mule accounts.

**Victim Profile:**
- Any user. SIM swap targets people with known high balances.
- The legitimate user suddenly cannot use their phone (SIM deactivated).

**Synthetic Signals:**
| Signal | Value |
|--------|-------|
| `new_device_flag` | True |
| `new_city_flag` | True |
| `sim_swap_flag` | True (simulated: SIM change within last 24 hours) |
| `payee_first_seen_days` | 0 (all new payees) |
| `user_txn_velocity_1h` | Elevated (draining the account) |
| `amount_z_score` | High |
| `hour_deviation` | Possibly high (unusual login time) |

**Parameters:**
- All three flags active: new device, new city, SIM swap
- Amount range: ₹5,000–₹100,000
- Multiple transfers within 30 minutes
- Target mule accounts (young, high pass-through)

**Detection Hints:**
- Triple signal (new device + new city + SIM swap) is extremely rare for genuine users.
- Combined with new payees and high amounts → near-certain fraud.
- Genuine exception: phone upgrade + travel — but SIM swap flag distinguishes.

---

## Hard Negatives (Genuine Edge Cases)

The generator also produces the following legitimate-but-suspicious-looking transactions to test false positive resilience:

| Hard Negative | Why It Looks Suspicious |
|---------------|------------------------|
| **Rent payment** | Large amount, monthly, often to a relatively new payee (new landlord) |
| **Gold/jewellery purchase** | Very large amount at a merchant, first-time payee |
| **Hospital emergency** | Large, off-hours, new payee, high urgency |
| **New device after phone upgrade** | New device flag, but same city, same payees |
| **Travel to new city** | New city flag, transactions at new merchants |
| **First payment to new relative** | New payee, moderate-to-large amount (wedding gift, etc.) |
| **Salary payout by small business** | Rapid multiple payments to different payees (looks like burst) |
| **Festival season shopping** | Multiple new merchants, higher-than-usual amounts |

Each hard negative has specific generation logic to ensure the model cannot trivially distinguish them from fraud without the right feature combinations.
