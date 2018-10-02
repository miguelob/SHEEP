#include <memory>

#include <cstdint>
#include <cassert>
#include <algorithm>
#include "context-helib.hpp"
#include "circuit-repo.hpp"
#include "circuit-test-util.hpp"


int main(void) {
	using namespace SHEEP;
  
	ContextHElib_Fp<uint8_t> ctx;

	std::vector<ContextHElib_Fp<uint8_t>::Plaintext> pt_input = {55, 130};
	ContextHElib_Fp<uint8_t>::Ciphertext ct = ctx.encrypt(pt_input);

	long const_val = 2;

	// Perform operation
	ContextHElib_Fp<uint8_t>::Ciphertext ct_out = ctx.MultByConstant(ct, const_val);
	
	// Decrypt
	std::vector<ContextHElib_Fp<uint8_t>::Plaintext> pt_out = ctx.decrypt(ct_out);

	assert(pt_out[0] == 110);
	assert(pt_out[1] == 4);
}
