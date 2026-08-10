// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title EventTicket - Simplified NFT-based Event Ticketing (ERC721-like)
/// @notice Hop dong demo/hoc tap. Khong hoan toan tuan thu chuan ERC721/ERC165,
///         nhung the hien day du logic nghiep vu: mint ve, check-in, ban lai co gioi han gia.
contract EventTicket {
    string public eventName;
    address public organizer;
    uint256 public maxResalePercent = 110; // toi da 110% gia goc khi ban lai
    uint256 private _nextTokenId = 1;

    struct Ticket {
        uint256 seatId;
        uint256 originalPrice;
        bool checkedIn;
        address currentOwner;
    }

    mapping(uint256 => Ticket) public tickets;
    mapping(address => bool) public staff;
    mapping(address => uint256[]) private _ownedTokens;

    event TicketMinted(uint256 indexed tokenId, address indexed to, uint256 seatId, uint256 price);
    event TicketCheckedIn(uint256 indexed tokenId, address indexed staffMember);
    event TicketTransferred(uint256 indexed tokenId, address indexed from, address indexed to, uint256 price);
    event StaffUpdated(address indexed account, bool isStaff);

    modifier onlyOrganizer() {
        require(msg.sender == organizer, "Chi ban to chuc moi co quyen");
        _;
    }

    modifier onlyStaffOrOrganizer() {
        require(staff[msg.sender] || msg.sender == organizer, "Chi nhan vien moi co quyen");
        _;
    }

    constructor(string memory _eventName) {
        eventName = _eventName;
        organizer = msg.sender;
        staff[msg.sender] = true;
    }

    /// @notice Cap/thu quyen nhan vien check-in
    function setStaff(address account, bool isStaff) external onlyOrganizer {
        staff[account] = isStaff;
        emit StaffUpdated(account, isStaff);
    }

    /// @notice Ban to chuc phat hanh ve moi truc tiep vao vi nguoi mua
    function mintTicket(address to, uint256 seatId, uint256 price) external onlyOrganizer returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        tickets[tokenId] = Ticket({
            seatId: seatId,
            originalPrice: price,
            checkedIn: false,
            currentOwner: to
        });
        _ownedTokens[to].push(tokenId);
        emit TicketMinted(tokenId, to, seatId, price);
        return tokenId;
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = tickets[tokenId].currentOwner;
        require(owner != address(0), "Ve khong ton tai");
        return owner;
    }

    function ticketsOf(address account) external view returns (uint256[] memory) {
        return _ownedTokens[account];
    }

    /// @notice Nhan vien quet QR va goi ham nay de check-in, ve chi duoc dung 1 lan
    function checkIn(uint256 tokenId) external onlyStaffOrOrganizer {
        require(tickets[tokenId].currentOwner != address(0), "Ve khong ton tai");
        require(!tickets[tokenId].checkedIn, "Ve da duoc su dung");
        tickets[tokenId].checkedIn = true;
        emit TicketCheckedIn(tokenId, msg.sender);
    }

    /// @notice Chuyen nhuong/ban lai ve, gioi han gia ban lai theo maxResalePercent.
    /// Trong mo hinh nay, backend (giu key ban to chuc) thuc hien transfer thay nguoi dung
    /// sau khi da xac nhan thanh toan off-chain - phu hop voi vi "embedded wallet" tren mobile.
    function transferTicket(uint256 tokenId, address from, address to, uint256 price) external onlyOrganizer {
        require(tickets[tokenId].currentOwner == from, "Nguoi ban khong phai chu ve");
        require(!tickets[tokenId].checkedIn, "Ve da su dung, khong the ban lai");
        uint256 maxPrice = (tickets[tokenId].originalPrice * maxResalePercent) / 100;
        require(price <= maxPrice, "Gia vuot qua gioi han cho phep");

        uint256[] storage fromTokens = _ownedTokens[from];
        for (uint256 i = 0; i < fromTokens.length; i++) {
            if (fromTokens[i] == tokenId) {
                fromTokens[i] = fromTokens[fromTokens.length - 1];
                fromTokens.pop();
                break;
            }
        }
        _ownedTokens[to].push(tokenId);
        tickets[tokenId].currentOwner = to;
        emit TicketTransferred(tokenId, from, to, price);
    }

    function getTicket(uint256 tokenId) external view returns (
        uint256 seatId,
        uint256 originalPrice,
        bool checkedIn,
        address currentOwner
    ) {
        Ticket memory t = tickets[tokenId];
        return (t.seatId, t.originalPrice, t.checkedIn, t.currentOwner);
    }
}
