pragma solidity 0.8.17;

import {IERC3156FlashBorrower} from "../../packages/contracts/contracts/Interfaces/IERC3156FlashBorrower.sol";
import {IERC3156FlashLender} from "../../packages/contracts/contracts/Interfaces/IERC3156FlashLender.sol";
import {IEBTCToken} from "../../packages/contracts/contracts/Interfaces/IEBTCToken.sol";

contract MockFlashBorrower is IERC3156FlashBorrower {
  enum Action {
    MINT,
    BURN,
    APPROVE,
    TRANSFER,
    TRANSFER_FROM,
    INCREASE_ALLOWANCE,
    DECREASE_ALLOWANCE,
    OTHER
  }

  Action public action;
  uint8 public counter;
  uint8 public repeat_on_count;
  address public transferTo;
  address public spender;

  constructor(IERC3156FlashLender lender) {
    _lender = lender;
    allowRepayment = true;
  }

  /// @dev ERC-3156 Flash loan callback
  function onFlashLoan(
    address /*initiator*/,
    address token,
    uint256 amount,
    uint256 /*fee*/,
    bytes calldata /*data*/
  ) external override returns (bytes32) {
    counter++;
    if (action == Action.APPROVE) {
        token.approve(spender, amount);
    } else if (action == Action.TRANSFER) {
        token.transfer(transferTo, amount);
    } else if (action == Action.MINT) {
        token.mint(transferTo, amount);
    } else if (action == Action.BURN) {
        token.burn(transferTo, amount);
    } else if (action == Action.TRANSFER_FROM) {
        token.transferFrom(spender, transferTo, amount);
    }   else if (action == Action.OTHER) {
        require(true);
    }
    return keccak256('ERC3156FlashBorrower.onFlashLoan');
  }
}