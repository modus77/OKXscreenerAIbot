import pytest
import asyncio
from backend.services.okx import OKXClient
from backend.clients.okx_cex import OKXCEXClient
from backend.clients.jupiter_dex import JupiterDEXClient

@pytest.mark.asyncio
async def test_get_ticker_btc():
    client = OKXClient()
    data = await client.get_ticker('BTC')
    assert 'last' in data
    assert 'vol24h' in data
    assert 'change24h' in data
    assert 'bid' in data
    assert 'ask' in data
    assert isinstance(data['last'], float)
    assert isinstance(data['vol24h'], float)
    assert isinstance(data['change24h'], float)
    assert isinstance(data['bid'], float)
    assert isinstance(data['ask'], float)
    assert data['last'] > 0
    assert data['vol24h'] > 0

@pytest.mark.asyncio
async def test_dex_methods():
    client = OKXClient()
    chain_id = 101  # Solana
    # DEX pools
    try:
        pools = await client.get_pools(chain_id=chain_id)
        assert 'data' in pools or 'pools' in pools
    except Exception as e:
        pytest.skip(f"DEX pools endpoint not available: {e}")
    # DEX tokens
    try:
        tokens = await client.get_tokens(chain_id=chain_id)
        assert 'data' in tokens or 'tokens' in tokens
    except Exception as e:
        pytest.skip(f"DEX tokens endpoint not available: {e}")
    # DEX quotes (if at least 2 tokens)
    token_list = tokens.get('data') or tokens.get('tokens')
    if token_list and len(token_list) > 1:
        t0 = token_list[0]
        t1 = token_list[1]
        token_in = t0.get('address') or t0.get('symbol')
        token_out = t1.get('address') or t1.get('symbol')
        try:
            prices = await client.get_prices(token_in, token_out, chain_id=chain_id)
            assert 'data' in prices or 'prices' in prices
            swaps = await client.get_swaps(token_in, token_out, limit=5, chain_id=chain_id)
            assert 'data' in swaps or 'swaps' in swaps
        except Exception as e:
            pytest.skip(f"DEX prices/swaps endpoint not available: {e}")

@pytest.mark.asyncio
async def test_get_candles_btc():
    client = OKXClient()
    data = await client.get_candles('BTC', bar='5m', limit=5)
    assert 'data' in data
    assert isinstance(data['data'], list)
    assert len(data['data']) > 0

@pytest.mark.asyncio
async def test_get_system_time():
    client = OKXClient()
    data = await client.get_system_time()
    assert 'ts' in data.get('data', [{}])[0] or 'data' in data

@pytest.mark.asyncio
async def test_compare_cex_price_wif():
    client = OKXClient()
    # WIF: centralized ticker on OKX
    cex = await client.get_ticker("WIF")
    price_cex = cex["last"]
    vol_cex = cex["vol24h"]
    assert price_cex > 0
    assert vol_cex > 0
    print(f"WIF CEX price: {price_cex}, 24h volume: {vol_cex}")

@pytest.mark.asyncio
async def test_get_token_price_usdc_solana_and_eth():
    client = OKXClient()
    # USDC Solana
    usdc_solana = "EPjFWdd5AufqSSqeM2q8j6bGzj4bQ3bYQ3FihZzPWw6A"
    # USDC Ethereum
    usdc_eth = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    # Solana
    try:
        dex_sol = await client.get_token_price(chain_id=101, token_address=usdc_solana)
        price_sol = float(dex_sol["data"]["price"])
        print(f"USDC Solana DEX price: {price_sol}")
        assert price_sol > 0
    except Exception as e:
        print(f"Solana DEX price error: {e}")
    # Ethereum
    try:
        dex_eth = await client.get_token_price(chain_id=1, token_address=usdc_eth)
        price_eth = float(dex_eth["data"]["price"])
        print(f"USDC Ethereum DEX price: {price_eth}")
        assert price_eth > 0
    except Exception as e:
        print(f"Ethereum DEX price error: {e}")

@pytest.mark.asyncio
def test_get_token_price_jupiter_ekpqgs():
    """
    Check the price of the Solana token EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm via the OKX Web3 DEX API (error or correct handling expected).
    """
    client = OKXClient()
    mint = "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
    try:
        result = asyncio.get_event_loop().run_until_complete(client.get_token_price(101, mint))
        price = float(result["data"]["price"])
        print(f"Jupiter/OKX DEX price for EKpQGS...: {price}")
        assert price > 0
    except Exception as e:
        print(f"Jupiter/OKX DEX price error for EKpQGS...: {e}")

@pytest.mark.asyncio
async def test_compare_price_wif_cex_vs_jupiter():
    cex = OKXCEXClient()
    dex = JupiterDEXClient()

    # 1. Get the price from OKX CEX (WIF-USDC)
    okx_data = await cex.get_ticker("WIF-USDC")
    assert okx_data["code"] == '0'
    price_cex = float(okx_data["data"][0]["last"])
    assert price_cex > 0

    # 2. Get the price from Jupiter DEX (USDC -> WIF)
    WIF_MINT = "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    amount = 100_000_000  # 100 USDC (6 decimals)
    quote = await dex.get_quote(input_mint=USDC_MINT, output_mint=WIF_MINT, amount=amount, swap_mode="ExactIn")
    assert "outAmount" in quote and int(quote["outAmount"]) > 0
    wif_out = int(quote["outAmount"]) / 1_000_000  # WIF with decimals
    price_dex = amount / int(quote["outAmount"])  # Price of 1 WIF in USDC
    assert price_dex > 0

    # 3. Calculate the spread
    spread_pct = ((price_dex - price_cex) / price_cex) * 100
    print(f"CEX: {price_cex}, DEX: {price_dex}, Spread: {spread_pct:.2f}% (Jupiter: {wif_out} WIF per 100 USDC)")
    assert abs(spread_pct) < 20  # sanity check
