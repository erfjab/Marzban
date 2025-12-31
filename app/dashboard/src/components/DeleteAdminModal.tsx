import {
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Text,
  useToast,
} from "@chakra-ui/react";
import { FetchAdminsQueryKey, useAdmins } from "contexts/AdminsContext";
import { FC } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useMutation, useQueryClient } from "react-query";
import {
  generateErrorMessage,
  generateSuccessMessage,
} from "utils/toastHandler";
import { DeleteIcon, DeleteUserModalProps } from "./DeleteUserModal";
import { Icon } from "./Icon";

export const DeleteAdminModal: FC<DeleteUserModalProps> = ({
  deleteCallback,
}) => {
  const { deleteAdmin, deletingAdmin, setDeletingAdmin } = useAdmins();
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const onClose = () => {
    setDeletingAdmin(null);
  };

  const { isLoading, mutate: onDelete } = useMutation(deleteAdmin, {
    onSuccess: () => {
      generateSuccessMessage(
        t("deleteAdmin.deleteSuccess", {username: deletingAdmin && deletingAdmin.username}),
        toast
      );
      setDeletingAdmin(null);
      queryClient.invalidateQueries(FetchAdminsQueryKey);
      deleteCallback && deleteCallback();
    },
    onError: (e) => {
      generateErrorMessage(e, toast);
    },
  });

  return (
    <Modal isCentered isOpen={!!deletingAdmin} onClose={onClose} size="sm">
      <ModalOverlay bg="blackAlpha.300" backdropFilter="blur(10px)" />
      <ModalContent mx="3">
        <ModalHeader pt={6}>
          <Icon color="red">
            <DeleteIcon />
          </Icon>
        </ModalHeader>
        <ModalCloseButton mt={3} />
        <ModalBody>
          <Text fontWeight="semibold" fontSize="lg">
            {t("deleteAdmin.title")}
          </Text>
          {deletingAdmin && (
            <Text
              mt={1}
              fontSize="sm"
              _dark={{ color: "gray.400" }}
              color="gray.600"
            >
              <Trans components={{ b: <b /> }}>
                {t("deleteAdmin.prompt", {username: deletingAdmin.username})}
              </Trans>
            </Text>
          )}
        </ModalBody>
        <ModalFooter display="flex">
          <Button size="sm" onClick={onClose} mr={3} w="full" variant="outline">
            {t("cancel")}
          </Button>
          <Button
            size="sm"
            w="full"
            colorScheme="red"
            onClick={() => onDelete()}
            leftIcon={isLoading ? <Spinner size="xs" /> : undefined}
          >
            {t("delete")}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
